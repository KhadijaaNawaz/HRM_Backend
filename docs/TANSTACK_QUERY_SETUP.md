# TanStack Query (React Query) Setup Guide for HRM SaaS

Complete setup for API integration using TanStack Query with the HRM SaaS backend.

---

## Installation

```bash
npm install @tanstack/react-query@latest
npm install axios
```

---

## 1. Query Client Setup

### Create Query Client with Error Handling

```typescript
// src/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes (previously cacheTime)
      retry: (failureCount, error) => {
        // Don't retry on 401 (unauthorized) or 403 (forbidden)
        if (error && typeof error === 'object' && 'status' in error) {
          const status = (error as { status: number }).status;
          if (status === 401 || status === 403) return false;
        }
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
      refetchOnMount: false,
    },
    mutations: {
      retry: false,
    },
  },
});
```

---

## 2. Query Keys Factory

```typescript
// src/lib/query-keys.ts
export const queryKeys = {
  // Auth
  auth: ['auth'] as const,
  currentUser: ['currentUser'] as const,

  // Users
  users: (filters?: { page?: number; search?: string }) =>
    filters ? ['users', filters] : ['users'],
  user: (id: string) => ['users', id] as const,

  // Roles
  roles: ['roles'] as const,
  role: (id: string) => ['roles', id] as const,

  // Invitations
  invitations: (filters?: { status?: string }) =>
    filters ? ['invitations', filters] : ['invitations'],
  invitation: (id: string) => ['invitations', id] as const,

  // Attendance
  attendance: (filters?: { date_from?: string; date_to?: string; user_id?: string }) =>
    filters ? ['attendance', filters] : ['attendance'],
  todayAttendance: ['attendance', 'today'] as const,
  attendanceReport: (params?: { month?: number; year?: number; user_id?: string }) =>
    params ? ['attendance', 'report', params] : ['attendance', 'report'],
  attendanceSettings: ['attendance', 'settings'] as const,

  // Organization
  organization: ['organization'] as const,
  organizationSettings: ['organization', 'settings'] as const,

  // Audit Logs
  auditLogs: (filters?: { user_id?: string; action?: string; page?: number }) =>
    filters ? ['auditLogs', filters] : ['auditLogs'],

  // Admin
  tenants: ['tenants'] as const,
} as const;
```

---

## 3. API Client with Interceptors

```typescript
// src/lib/api-client.ts
import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Get tenant host from current URL
export const getTenantHost = (): string => {
  const hostname = window.location.hostname;

  // For local development with subdomains like acme.localhost:3000
  if (hostname.includes('.localhost')) {
    return hostname;
  }

  // Extract subdomain from production URL
  const parts = hostname.split('.');
  if (parts.length >= 2) {
    // For subdomain.example.com, return subdomain.example.com
    return hostname;
  }

  // Default fallback
  return hostname;
};

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Type definitions
export interface ApiError {
  detail?: string;
  message?: string;
  [key: string]: string | string[] | undefined;
}

export class ApiErrorClass extends Error {
  status?: number;
  fields?: Record<string, string>;

  constructor(message: string, status?: number, fields?: Record<string, string>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.fields = fields;
  }
}

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add Host header for tenant resolution
    config.headers['Host'] = getTenantHost();

    // Add Authorization header
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Track refresh token promise to prevent multiple refresh attempts
let refreshPromise: Promise<AxiosResponse> | null = null;

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // If we're already refreshing, wait for it
      if (refreshPromise) {
        try {
          const response = await refreshPromise;
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
          }
          return apiClient(originalRequest);
        } catch {
          // Refresh failed, continue to logout
        }
      }

      // Start token refresh
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        handleAuthError();
        return Promise.reject(error);
      }

      try {
        refreshPromise = axios.post(
          `${API_BASE_URL}/api/v1/auth/token/refresh/`,
          { refresh: refreshToken },
          {
            headers: {
              'Content-Type': 'application/json',
              'Host': getTenantHost(),
            },
          }
        );

        const response = await refreshPromise;
        const { access, refresh: newRefreshToken } = response.data;

        // Store new tokens
        localStorage.setItem('access_token', access);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }

        // Update header and retry
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }

        refreshPromise = null;
        return apiClient(originalRequest);
      } catch (refreshError) {
        refreshPromise = null;
        handleAuthError();
        return Promise.reject(refreshError);
      }
    }

    // Transform error to ApiErrorClass
    const apiError = new ApiErrorClass(
      error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred',
      error.response?.status,
      extractFieldErrors(error.response?.data)
    );

    return Promise.reject(apiError);
  }
);

// Helper function to extract field errors
function extractFieldErrors(data?: ApiError): Record<string, string> {
  const fields: Record<string, string> = {};
  if (!data) return fields;

  Object.entries(data).forEach(([key, value]) => {
    if (key !== 'detail' && key !== 'message') {
      if (typeof value === 'string') {
        fields[key] = value;
      } else if (Array.isArray(value)) {
        fields[key] = value[0];
      }
    }
  });

  return fields;
}

// Handle auth error - clear tokens and redirect
function handleAuthError() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  // Only redirect if not already on login page
  if (!window.location.pathname.includes('/login')) {
    window.location.href = '/login';
  }
}

export default apiClient;
```

---

## 4. API Services (for use with TanStack Query)

```typescript
// src/lib/api-services.ts
import apiClient, { ApiErrorClass } from './api-client';
import { queryKeys } from './query-keys';

// Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  is_active: boolean;
  is_tenant_admin: boolean;
  is_superuser: boolean;
  roles: Role[];
  profile_picture?: string;
  date_joined: string;
  last_login?: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system_role: boolean;
  created_at: string;
  updated_at: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: string;
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
  invited_by: string;
  created_at: string;
  expires_at: string;
}

export interface AttendanceRecord {
  id: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
  };
  date: string;
  check_in: string | null;
  check_out: string | null;
  status: 'present' | 'absent' | 'late' | 'half_day';
  work_hours: number;
  notes?: string;
}

export interface AttendanceReport {
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
  };
  period: {
    month: number;
    year: number;
    month_name: string;
  };
  summary: {
    total_days: number;
    present_days: number;
    absent_days: number;
    late_days: number;
    total_work_hours: number;
    average_work_hours: number;
    required_hours: number;
    overtime_hours: number;
    attendance_percentage: number;
  };
  daily_records: Array<{
    date: string;
    check_in: string;
    check_out: string;
    status: string;
    work_hours: number;
  }>;
}

// Auth Service
export const authService = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post<{
      access: string;
      refresh: string;
      user: User;
    }>('/api/v1/auth/login/', { email, password });

    // Store tokens
    localStorage.setItem('access_token', response.data.access);
    localStorage.setItem('refresh_token', response.data.refresh);

    return response.data;
  },

  logout: async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      await apiClient.post('/api/v1/auth/logout/', { refresh: refreshToken });
    }
    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me/');
    return response.data;
  },

  refreshToken: async (refreshToken: string) => {
    const response = await apiClient.post<{
      access: string;
      refresh?: string;
    }>('/api/v1/auth/token/refresh/', { refresh: refreshToken });
    return response.data;
  },

  changePassword: async (oldPassword: string, newPassword: string) => {
    await apiClient.post('/api/v1/auth/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  forgotPassword: async (email: string, redirectUrl: string) => {
    await apiClient.post('/api/v1/auth/password/forgot/', {
      email,
      redirect_url: redirectUrl,
    });
  },

  resetPassword: async (uid: string, token: string, newPassword: string) => {
    await apiClient.post('/api/v1/auth/password/reset/', {
      uid,
      token,
      new_password: newPassword,
    });
  },
};

// Users Service
export const usersService = {
  list: async (params?: { page?: number; page_size?: number; search?: string }) => {
    const response = await apiClient.get<{
      results: User[];
      count: number;
      next: string | null;
      previous: string | null;
    }>('/api/v1/users/', { params });
    return response.data;
  },

  get: async (id: string): Promise<User> => {
    const response = await apiClient.get<User>(`/api/v1/users/${id}/`);
    return response.data;
  },

  create: async (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone?: string;
    role_names?: string[];
  }): Promise<User> => {
    const response = await apiClient.post<User>('/api/v1/users/', data);
    return response.data;
  },

  update: async (
    id: string,
    data: {
      first_name?: string;
      last_name?: string;
      phone?: string;
      profile_picture?: string;
    }
  ): Promise<User> => {
    const response = await apiClient.patch<User>(`/api/v1/users/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/users/${id}/`);
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/users/me/');
    return response.data;
  },

  updateMe: async (data: {
    first_name?: string;
    last_name?: string;
    phone?: string;
    profile_picture?: string;
  }): Promise<User> => {
    const response = await apiClient.patch<User>('/api/v1/users/me/', data);
    return response.data;
  },
};

// Roles Service
export const rolesService = {
  list: async (): Promise<Role[]> => {
    const response = await apiClient.get<{ results: Role[] }>('/api/v1/roles/');
    return response.data.results;
  },

  get: async (id: string): Promise<Role> => {
    const response = await apiClient.get<Role>(`/api/v1/roles/${id}/`);
    return response.data;
  },

  create: async (data: { name: string; description: string }): Promise<Role> => {
    const response = await apiClient.post<Role>('/api/v1/roles/', data);
    return response.data;
  },

  update: async (
    id: string,
    data: { name?: string; description?: string }
  ): Promise<Role> => {
    const response = await apiClient.patch<Role>(`/api/v1/roles/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/roles/${id}/`);
  },

  assign: async (roleId: string, userId: string): Promise<void> => {
    await apiClient.post(`/api/v1/roles/${roleId}/assign/`, { user_id: userId });
  },

  revoke: async (roleId: string, userId: string): Promise<void> => {
    await apiClient.post(`/api/v1/roles/${roleId}/revoke/`, { user_id: userId });
  },
};

// Invitations Service
export const invitationsService = {
  list: async (params?: { status?: string; page?: number }) => {
    const response = await apiClient.get<{
      results: Invitation[];
      count: number;
    }>('/api/v1/invite/', { params });
    return response.data;
  },

  create: async (data: {
    email: string;
    role: string;
    redirect_url: string;
  }): Promise<Invitation> => {
    const response = await apiClient.post<Invitation>('/api/v1/invite/', data);
    return response.data;
  },

  accept: async (data: {
    token: string;
    password: string;
    first_name: string;
    last_name: string;
  }): Promise<void> => {
    await apiClient.post('/api/v1/invite/accept/', data);
  },

  cancel: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/invite/${id}/`);
  },

  resend: async (email: string): Promise<void> => {
    await apiClient.post('/api/v1/invite/resend/', { email });
  },
};

// Attendance Service
export const attendanceService = {
  list: async (params?: {
    user_id?: string;
    date_from?: string;
    date_to?: string;
    status?: string;
    page?: number;
  }) => {
    const response = await apiClient.get<{
      results: AttendanceRecord[];
      count: number;
    }>('/api/v1/attendance/', { params });
    return response.data;
  },

  checkIn: async (data?: {
    notes?: string;
    latitude?: number;
    longitude?: number;
  }): Promise<AttendanceRecord> => {
    const response = await apiClient.post<AttendanceRecord>(
      '/api/v1/attendance/check-in/',
      data || {}
    );
    return response.data;
  },

  checkOut: async (data?: {
    notes?: string;
    latitude?: number;
    longitude?: number;
  }): Promise<AttendanceRecord> => {
    const response = await apiClient.post<AttendanceRecord>(
      '/api/v1/attendance/check-out/',
      data || {}
    );
    return response.data;
  },

  getReport: async (params?: {
    user_id?: string;
    month?: number;
    year?: number;
  }): Promise<AttendanceReport> => {
    const response = await apiClient.get<AttendanceReport>(
      '/api/v1/attendance/report/',
      { params }
    );
    return response.data;
  },

  getSettings: async () => {
    const response = await apiClient.get<{
      workdays: string[];
      monthly_required_days: number;
      check_in_start_time: string;
      check_in_end_time: string;
      late_grace_minutes: number;
    }>('/api/v1/attendance/settings/');
    return response.data;
  },
};

// Organization Service
export const organizationService = {
  getOverview: async () => {
    const response = await apiClient.get<{
      organization: {
        id: string;
        name: string;
        slug: string;
        status: string;
        timezone: string;
      };
      stats: {
        total_users: number;
        active_users: number;
        total_roles: number;
        pending_invitations: number;
      };
    }>('/api/v1/organization/overview/');
    return response.data;
  },

  getSettings: async () => {
    const response = await apiClient.get<{
      id: string;
      name: string;
      slug: string;
      status: string;
      timezone: string;
      workdays: string[];
      monthly_required_days: number;
      public_signup_enabled: boolean;
    }>('/api/v1/organization/settings/');
    return response.data;
  },

  updateSettings: async (data: {
    timezone?: string;
    workdays?: string[];
    monthly_required_days?: number;
  }) => {
    const response = await apiClient.patch('/api/v1/organization/settings/', data);
    return response.data;
  },
};

// Admin Service (Superuser only)
export const adminService = {
  createTenant: async (data: {
    name: string;
    slug: string;
    domain: string;
    admin_email: string;
    admin_password: string;
    admin_first_name: string;
    admin_last_name: string;
  }) => {
    const response = await apiClient.post('/api/v1/admin/create-tenant/', data);
    return response.data;
  },

  listTenants: async () => {
    const response = await apiClient.get('/api/v1/admin/tenants/');
    return response.data;
  },
};
```

---

## 5. Custom Hooks for TanStack Query

```typescript
// src/hooks/use-auth.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService, queryKeys } from '@/lib/api-services';
import { useNavigate } from 'react-router-dom';

export function useLogin() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: (data) => {
      // Set user data in query cache
      queryClient.setQueryData(queryKeys.currentUser, data.user);
      // Navigate to dashboard
      navigate('/dashboard');
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: authService.logout,
    onSuccess: () => {
      // Clear all query cache
      queryClient.clear();
      // Navigate to login
      navigate('/login');
    },
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: authService.getCurrentUser,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: ({ oldPassword, newPassword }: { oldPassword: string; newPassword: string }) =>
      authService.changePassword(oldPassword, newPassword),
    onSuccess: () => {
      // Show success message
      alert('Password changed successfully');
    },
  });
}
```

```typescript
// src/hooks/use-users.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersService, queryKeys, User } from '@/lib/api-services';

export function useUsers(params?: { page?: number; search?: string }) {
  return useQuery({
    queryKey: queryKeys.users(params),
    queryFn: () => usersService.list(params),
  });
}

export function useUser(id: string) {
  return useQuery({
    queryKey: queryKeys.user(id),
    queryFn: () => usersService.get(id),
    enabled: !!id,
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users() });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<User> }) =>
      usersService.update(id, data),
    onSuccess: (_, variables) => {
      // Invalidate specific user query
      queryClient.invalidateQueries({ queryKey: queryKeys.user(variables.id) });
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: queryKeys.users() });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users() });
    },
  });
}

export function useUpdateMe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: usersService.updateMe,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
    },
  });
}
```

```typescript
// src/hooks/use-attendance.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceService, queryKeys } from '@/lib/api-services';

export function useAttendance(filters?: {
  date_from?: string;
  date_to?: string;
  user_id?: string;
}) {
  return useQuery({
    queryKey: queryKeys.attendance(filters),
    queryFn: () => attendanceService.list(filters),
  });
}

export function useTodayAttendance() {
  const today = new Date().toISOString().split('T')[0];
  return useQuery({
    queryKey: queryKeys.todayAttendance,
    queryFn: async () => {
      const result = await attendanceService.list({
        date_from: today,
        date_to: today,
      });
      return result.results[0] || null;
    },
  });
}

export function useCheckIn() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: attendanceService.checkIn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.todayAttendance });
      queryClient.invalidateQueries({ queryKey: queryKeys.attendance() });
    },
  });
}

export function useCheckOut() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: attendanceService.checkOut,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.todayAttendance });
      queryClient.invalidateQueries({ queryKey: queryKeys.attendance() });
    },
  });
}

export function useAttendanceReport(params?: {
  month?: number;
  year?: number;
  user_id?: string;
}) {
  return useQuery({
    queryKey: queryKeys.attendanceReport(params),
    queryFn: () => attendanceService.getReport(params),
    enabled: !!params?.month && !!params?.year,
  });
}

export function useAttendanceSettings() {
  return useQuery({
    queryKey: queryKeys.attendanceSettings,
    queryFn: attendanceService.getSettings,
  });
}
```

```typescript
// src/hooks/use-invitations.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invitationsService, queryKeys } from '@/lib/api-services';

export function useInvitations(filters?: { status?: string }) {
  return useQuery({
    queryKey: queryKeys.invitations(filters),
    queryFn: () => invitationsService.list(filters),
  });
}

export function useCreateInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: invitationsService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.invitations() });
    },
  });
}

export function useCancelInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: invitationsService.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.invitations() });
    },
  });
}

export function useResendInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: invitationsService.resend,
  });
}

export function useAcceptInvitation() {
  return useMutation({
    mutationFn: invitationsService.accept,
  });
}
```

```typescript
// src/hooks/use-roles.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { rolesService, queryKeys } from '@/lib/api-services';

export function useRoles() {
  return useQuery({
    queryKey: queryKeys.roles,
    queryFn: rolesService.list,
  });
}

export function useCreateRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: rolesService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.roles });
    },
  });
}

export function useDeleteRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: rolesService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.roles });
    },
  });
}

export function useAssignRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ roleId, userId }: { roleId: string; userId: string }) =>
      rolesService.assign(roleId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users() });
    },
  });
}

export function useRevokeRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ roleId, userId }: { roleId: string; userId: string }) =>
      rolesService.revoke(roleId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users() });
    },
  });
}
```

---

## 6. App Provider Setup

```typescript
// src/App.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { queryClient } from './lib/query-client';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useCurrentUser } from './hooks/use-auth';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import UsersPage from './pages/UsersPage';
import AttendancePage from './pages/AttendancePage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading, isError } = useCurrentUser();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (isError || !user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <UsersPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/attendance"
            element={
              <ProtectedRoute>
                <AttendancePage />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
```

---

## 7. Usage Examples

### Login Page

```typescript
// src/pages/LoginPage.tsx
import { useState } from 'react';
import { useLogin } from '@/hooks/use-auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const login = useLogin();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login.mutate({ email, password });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit" disabled={login.isPending}>
        {login.isPending ? 'Logging in...' : 'Login'}
      </button>
      {login.error && <p>{login.error.message}</p>}
    </form>
  );
}
```

### Users List

```typescript
// src/pages/UsersPage.tsx
import { useUsers, useDeleteUser } from '@/hooks/use-users';

export default function UsersPage() {
  const { data, isLoading } = useUsers({ page: 1 });
  const deleteUser = useDeleteUser();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {data?.results.map((user) => (
          <li key={user.id}>
            {user.email}
            <button
              onClick={() => deleteUser.mutate(user.id)}
              disabled={deleteUser.isPending}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Attendance Actions

```typescript
// src/components/AttendanceActions.tsx
import { useTodayAttendance, useCheckIn, useCheckOut } from '@/hooks/use-attendance';

export default function AttendanceActions() {
  const { data: todayAttendance, isLoading } = useTodayAttendance();
  const checkIn = useCheckIn();
  const checkOut = useCheckOut();

  if (isLoading) return <div>Loading...</div>;

  const hasCheckedIn = todayAttendance?.check_in && !todayAttendance?.check_out;

  return (
    <div>
      {hasCheckedIn ? (
        <button onClick={() => checkOut.mutate()} disabled={checkOut.isPending}>
          {checkOut.isPending ? 'Checking out...' : 'Check Out'}
        </button>
      ) : (
        <button onClick={() => checkIn.mutate()} disabled={checkIn.isPending}>
          {checkIn.isPending ? 'Checking in...' : 'Check In'}
        </button>
      )}
    </div>
  );
}
```

---

## 8. DevTools Installation (Optional)

```bash
npm install @tanstack/react-query-devtools
```

---

This setup provides a complete, production-ready TanStack Query integration for the HRM SaaS backend.
