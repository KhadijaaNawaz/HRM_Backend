# HRM SaaS API - Complete Frontend Implementation Guide

This guide provides complete instructions for implementing the HRM SaaS frontend with all API integrations.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Tech Stack Recommendations](#tech-stack-recommendations)
3. [Project Setup](#project-setup)
4. [Authentication Implementation](#authentication-implementation)
5. [API Client Setup](#api-client-setup)
6. [State Management](#state-management)
7. [Component Implementation](#component-implementation)
8. [Error Handling](#error-handling)
9. [Complete Code Examples](#complete-code-examples)

---

## Architecture Overview

### Multi-Tenancy Architecture

The HRM SaaS uses **subdomain-based multi-tenancy**:
- Each tenant (organization) has its own subdomain (e.g., `acme.localhost`, `techcorp.localhost`)
- The backend uses the `Host` header to determine which tenant's data to serve
- Users are completely isolated between tenants

### Authentication Flow

```
1. User enters email/password on login page
2. Frontend sends POST /api/v1/auth/login/ with Host header
3. Backend validates credentials and returns JWT tokens
4. Frontend stores tokens (access & refresh) securely
5. Frontend includes access token in Authorization header for all requests
6. When access token expires, use refresh token to get new access token
7. On logout, blacklist the refresh token
```

### Role-Based Access Control (4-Tier Hierarchy)

| Role | Permissions |
|------|-------------|
| **Superuser** | Platform-level admin, manages all tenants |
| **Tenant Admin** | Full access within tenant organization |
| **HR** | User management, attendance tracking, invitations |
| **Employee** | Self-service (own attendance, profile) |

---

## Tech Stack Recommendations

### Option 1: React + TypeScript + React Query (Recommended)

```
- React 18+ with TypeScript
- React Query (TanStack Query) for API state management
- React Router v6 for routing
- Axios for HTTP client
- Zustand or Context API for global state
- TailwindCSS for styling
- React Hook Form for forms
- Zod for validation
```

### Option 2: Vue 3 + TypeScript + Pinia

```
- Vue 3 with TypeScript
- Pinia for state management
- Vue Router 4 for routing
- Axios for HTTP client
- Element Plus or PrimeVue for UI components
```

### Option 3: Next.js (Full-Stack)

```
- Next.js 14+ with App Router
- TypeScript
- React Query for API state
- NextAuth.js for auth (custom JWT integration)
- shadcn/ui or NextUI for components
```

---

## Project Setup

### React + TypeScript Example

```bash
# Create new project
npm create vite@latest hrm-saas-frontend -- --template react-ts
cd hrm-saas-frontend

# Install dependencies
npm install @tanstack/react-query@latest
npm install axios react-router-dom zustand
npm install react-hook-form @hookform/resolvers zod
npm install date-fns clsx tailwind-merge
npm install @headlessui/react @heroicons/react

# Install dev dependencies
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### Tailwind Configuration

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
      },
    },
  },
  plugins: [],
}
```

---

## API Client Setup

### 1. Create Axios Instance with Interceptors

```typescript
// src/lib/api-client.ts
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Get tenant domain from current URL
const getTenantHost = (): string => {
  // In development: extract subdomain from localhost URL
  // In production: use actual host
  const hostname = window.location.hostname;

  // For local development with subdomains like acme.localhost:3000
  if (hostname.includes('.localhost')) {
    return hostname;
  }

  // For production
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

// Request interceptor - add auth token and host header
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add Host header for tenant resolution
    config.headers['Host'] = getTenantHost();

    // Add Authorization header if token exists
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const response = await axios.post(
          `${API_BASE_URL}/api/v1/auth/token/refresh/`,
          { refresh: refreshToken },
          {
            headers: {
              'Content-Type': 'application/json',
              'Host': getTenantHost(),
            },
          }
        );

        const { access, refresh: newRefreshToken } = response.data;

        // Store new tokens
        localStorage.setItem('access_token', access);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }

        // Update authorization header
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }

        // Retry original request
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed - logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### 2. Create API Service Functions

```typescript
// src/lib/api.ts
import apiClient from './api-client';

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
  organization?: Organization;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system_role: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  status: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface AttendanceRecord {
  id: string;
  user: { id: string; email: string; first_name: string; last_name: string };
  date: string;
  check_in: string | null;
  check_out: string | null;
  status: 'present' | 'absent' | 'late' | 'half_day';
  work_hours: number;
  notes?: string;
}

// Auth APIs
export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login/', data);
    return response.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout/', { refresh: refreshToken });
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me/');
    return response.data;
  },

  refreshToken: async (refreshToken: string): Promise<{ access: string; refresh?: string }> => {
    const response = await apiClient.post('/api/v1/auth/token/refresh/', { refresh: refreshToken });
    return response.data;
  },

  changePassword: async (data: { old_password: string; new_password: string }): Promise<void> => {
    await apiClient.post('/api/v1/auth/password/change/', data);
  },

  forgotPassword: async (data: { email: string; redirect_url: string }): Promise<void> => {
    await apiClient.post('/api/v1/auth/password/forgot/', data);
  },

  resetPassword: async (data: { uid: string; token: string; new_password: string }): Promise<void> => {
    await apiClient.post('/api/v1/auth/password/reset/', data);
  },
};

// User APIs
export const userApi = {
  list: async (params?: { page?: number; page_size?: number }): Promise<{ results: User[]; count: number }> => {
    const response = await apiClient.get('/api/v1/users/', { params });
    return response.data;
  },

  get: async (id: string): Promise<User> => {
    const response = await apiClient.get(`/api/v1/users/${id}/`);
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

  update: async (id: string, data: Partial<User>): Promise<User> => {
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

  updateMe: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch<User>('/api/v1/users/me/', data);
    return response.data;
  },
};

// Role APIs
export const roleApi = {
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

  update: async (id: string, data: { name?: string; description?: string }): Promise<Role> => {
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

// Invitation APIs
export interface Invitation {
  id: string;
  email: string;
  role: string;
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
  invited_by: string;
  created_at: string;
  expires_at: string;
  token?: string;
}

export const invitationApi = {
  list: async (params?: { status?: string; page?: number }): Promise<{ results: Invitation[]; count: number }> => {
    const response = await apiClient.get('/api/v1/invite/', { params });
    return response.data;
  },

  create: async (data: { email: string; role: string; redirect_url: string }): Promise<Invitation> => {
    const response = await apiClient.post<Invitation>('/api/v1/invite/', data);
    return response.data;
  },

  accept: async (data: { token: string; password: string; first_name: string; last_name: string }): Promise<void> => {
    await apiClient.post('/api/v1/invite/accept/', data);
  },

  cancel: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/invite/${id}/`);
  },

  resend: async (email: string): Promise<void> => {
    await apiClient.post('/api/v1/invite/resend/', { email });
  },
};

// Attendance APIs
export const attendanceApi = {
  list: async (params?: {
    user_id?: string;
    date_from?: string;
    date_to?: string;
    status?: string;
    page?: number;
  }): Promise<{ results: AttendanceRecord[]; count: number }> => {
    const response = await apiClient.get('/api/v1/attendance/', { params });
    return response.data;
  },

  checkIn: async (data?: { notes?: string; latitude?: number; longitude?: number }): Promise<AttendanceRecord> => {
    const response = await apiClient.post<AttendanceRecord>('/api/v1/attendance/check-in/', data || {});
    return response.data;
  },

  checkOut: async (data?: { notes?: string; latitude?: number; longitude?: number }): Promise<AttendanceRecord> => {
    const response = await apiClient.post<AttendanceRecord>('/api/v1/attendance/check-out/', data || {});
    return response.data;
  },

  getReport: async (params?: { user_id?: string; month?: number; year?: number }): Promise<any> => {
    const response = await apiClient.get('/api/v1/attendance/report/', { params });
    return response.data;
  },

  getSettings: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/attendance/settings/');
    return response.data;
  },
};

// Organization APIs
export const organizationApi = {
  getOverview: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/organization/overview/');
    return response.data;
  },

  getSettings: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/organization/settings/');
    return response.data;
  },

  updateSettings: async (data: {
    timezone?: string;
    workdays?: string[];
    monthly_required_days?: number;
  }): Promise<any> => {
    const response = await apiClient.patch('/api/v1/organization/settings/', data);
    return response.data;
  },
};

// Admin APIs (Superuser only)
export const adminApi = {
  createTenant: async (data: {
    name: string;
    slug: string;
    domain: string;
    admin_email: string;
    admin_password: string;
    admin_first_name: string;
    admin_last_name: string;
  }): Promise<any> => {
    const response = await apiClient.post('/api/v1/admin/create-tenant/', data);
    return response.data;
  },

  listTenants: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/admin/tenants/');
    return response.data;
  },
};
```

---

## State Management

### 1. Auth Store (Zustand)

```typescript
// src/stores/auth-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/lib/api';

interface AuthState {
  user: User | null;
  access_token: string | null;
  refresh_token: string | null;
  isAuthenticated: boolean;
  setAuth: (tokens: { access: string; refresh: string }, user: User) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      access_token: null,
      refresh_token: null,
      isAuthenticated: false,

      setAuth: (tokens, user) => {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        set({
          user,
          access_token: tokens.access,
          refresh_token: tokens.refresh,
          isAuthenticated: true,
        });
      },

      setUser: (user) => set({ user }),

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({
          user: null,
          access_token: null,
          refresh_token: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        access_token: state.access_token,
        refresh_token: state.refresh_token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helper hooks
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useIsTenantAdmin = () => useAuthStore((state) => state.user?.is_tenant_admin || false);
export const useIsSuperuser = () => useAuthStore((state) => state.user?.is_superuser || false);
export const useHasRole = (roleName: string) =>
  useAuthStore((state) => state.user?.roles.some((r) => r.name === roleName) || false);
```

### 2. React Query Setup

```typescript
// src/lib/react-query.ts
import { QueryClient, QueryCache } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/auth-store';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
  queryCache: new QueryCache({
    onError: (error) => {
      // Handle global query errors
      if (error?.message?.includes('401')) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    },
  }),
});
```

---

## Authentication Implementation

### 1. Login Page Component

```typescript
// src/pages/LoginPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setAuth({ access: data.access, refresh: data.refresh }, data.user);
      navigate('/dashboard');
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    loginMutation.mutate({ email, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <input
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <input
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loginMutation.isPending ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <a href="/forgot-password" className="font-medium text-primary-600 hover:text-primary-500">
                Forgot your password?
              </a>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
```

### 2. Protected Route Component

```typescript
// src/components/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useIsAuthenticated } from '@/stores/auth-store';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireSuperuser?: boolean;
  requireTenantAdmin?: boolean;
  requireRole?: string;
}

export default function ProtectedRoute({
  children,
  requireSuperuser = false,
  requireTenantAdmin = false,
  requireRole,
}: ProtectedRouteProps) {
  const isAuthenticated = useIsAuthenticated();
  const isTenantAdmin = useAuthStore((state) => state.user?.is_tenant_admin || false);
  const isSuperuser = useAuthStore((state) => state.user?.is_superuser || false);
  const userRoles = useAuthStore((state) => state.user?.roles?.map((r) => r.name) || []);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requireSuperuser && !isSuperuser) {
    return <Navigate to="/unauthorized" replace />;
  }

  if (requireTenantAdmin && !isTenantAdmin && !isSuperuser) {
    return <Navigate to="/unauthorized" replace />;
  }

  if (requireRole && !userRoles.includes(requireRole) && !isSuperuser) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}
```

### 3. Logout Function

```typescript
// src/components/LogoutButton.tsx
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/stores/auth-store';

export default function LogoutButton() {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  const refresh_token = useAuthStore((state) => state.refresh_token);

  const logoutMutation = useMutation({
    mutationFn: () => authApi.logout(refresh_token!),
    onSettled: () => {
      logout();
      navigate('/login');
    },
  });

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  return (
    <button
      onClick={handleLogout}
      className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
    >
      Logout
    </button>
  );
}
```

---

## Component Implementation

### 1. User List Component (HR/Admin)

```typescript
// src/components/users/UserList.tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '@/lib/api';

export default function UserList() {
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: () => userApi.list({ page, page_size: 20 }),
  });

  const deleteMutation = useMutation({
    mutationFn: userApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Team Members</h3>
        <div className="mt-5">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Roles
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data?.results.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.first_name} {user.last_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {user.roles.map((role) => (
                      <span
                        key={role.id}
                        className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 mr-1"
                      >
                        {role.name}
                      </span>
                    ))}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => deleteMutation.mutate(user.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
```

### 2. Attendance Check In/Out Component

```typescript
// src/components/attendance/AttendanceActions.tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceApi } from '@/lib/api';

export default function AttendanceActions() {
  const queryClient = useQueryClient();

  const checkInMutation = useMutation({
    mutationFn: attendanceApi.checkIn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance'] });
      queryClient.invalidateQueries({ queryKey: ['todayAttendance'] });
    },
  });

  const checkOutMutation = useMutation({
    mutationFn: attendanceApi.checkOut,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance'] });
      queryClient.invalidateQueries({ queryKey: ['todayAttendance'] });
    },
  });

  const { data: todayAttendance } = useQuery({
    queryKey: ['todayAttendance'],
    queryFn: async () => {
      const today = new Date().toISOString().split('T')[0];
      const result = await attendanceApi.list({ date_from: today, date_to: today });
      return result.results[0] || null;
    },
  });

  const hasCheckedIn = todayAttendance?.check_in && !todayAttendance?.check_out;

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Today's Attendance</h3>

      {todayAttendance?.check_in ? (
        <div>
          <p className="text-sm text-gray-500 mb-4">
            Checked in at: {new Date(todayAttendance.check_in).toLocaleTimeString()}
          </p>
          {!todayAttendance.check_out ? (
            <button
              onClick={() => checkOutMutation.mutate()}
              disabled={checkOutMutation.isPending}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50"
            >
              {checkOutMutation.isPending ? 'Checking out...' : 'Check Out'}
            </button>
          ) : (
            <p className="text-sm text-gray-500">
              Checked out at: {new Date(todayAttendance.check_out).toLocaleTimeString()}
            </p>
          )}
        </div>
      ) : (
        <button
          onClick={() => checkInMutation.mutate()}
          disabled={checkInMutation.isPending}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
        >
          {checkInMutation.isPending ? 'Checking in...' : 'Check In'}
        </button>
      )}
    </div>
  );
}
```

### 3. Invitation Form Component

```typescript
// src/components/invitations/InvitationForm.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { invitationApi, roleApi } from '@/lib/api';

export default function InvitationForm() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('Employee');

  const { data: roles } = useQuery({
    queryKey: ['roles'],
    queryFn: roleApi.list,
  });

  const inviteMutation = useMutation({
    mutationFn: invitationApi.create,
    onSuccess: () => {
      setEmail('');
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
      alert('Invitation sent successfully!');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    inviteMutation.mutate({
      email,
      role,
      redirect_url: `${window.location.origin}/accept-invite`,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email Address
        </label>
        <input
          type="email"
          id="email"
          required
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <div>
        <label htmlFor="role" className="block text-sm font-medium text-gray-700">
          Role
        </label>
        <select
          id="role"
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          {roles?.map((r) => (
            <option key={r.id} value={r.name}>
              {r.name}
            </option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={inviteMutation.isPending}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
      >
        {inviteMutation.isPending ? 'Sending...' : 'Send Invitation'}
      </button>
    </form>
  );
}
```

---

## Error Handling

### 1. Error Boundary Component

```typescript
// src/components/ErrorBoundary.tsx
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Something went wrong</h1>
            <p className="text-gray-600 mb-4">{this.state.error?.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 2. API Error Handler Hook

```typescript
// src/hooks/useApiError.ts
import { useCallback } from 'react';
import { AxiosError } from 'axios';

interface ApiError {
  detail?: string;
  message?: string;
  [key: string]: string | string[] | undefined;
}

export function useApiError() {
  const getErrorMessage = useCallback((error: unknown): string => {
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as AxiosError<ApiError>;
      const data = axiosError.response?.data;

      if (data?.detail) return data.detail;
      if (data?.message) return data.message;

      // Handle field-specific errors
      if (data) {
        const firstField = Object.keys(data)[0];
        const fieldError = data[firstField];
        if (typeof fieldError === 'string') return fieldError;
        if (Array.isArray(fieldError)) return fieldError[0];
      }
    }

    if (error instanceof Error) return error.message;
    return 'An unexpected error occurred';
  }, []);

  const getErrorFields = useCallback((error: unknown): Record<string, string> => {
    if (error && typeof error === 'object' && 'response' in error) {
      const axiosError = error as AxiosError<ApiError>;
      const data = axiosError.response?.data;

      if (data && typeof data === 'object') {
        const fields: Record<string, string> = {};
        for (const [key, value] of Object.entries(data)) {
          if (key !== 'detail' && key !== 'message') {
            if (typeof value === 'string') fields[key] = value;
            if (Array.isArray(value)) fields[key] = value[0];
          }
        }
        return fields;
      }
    }

    return {};
  }, []);

  return { getErrorMessage, getErrorFields };
}
```

---

## Complete App Structure

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   ├── ForgotPasswordForm.tsx
│   │   └── ResetPasswordForm.tsx
│   ├── users/
│   │   ├── UserList.tsx
│   │   ├── UserForm.tsx
│   │   └── UserCard.tsx
│   ├── attendance/
│   │   ├── AttendanceActions.tsx
│   │   ├── AttendanceList.tsx
│   │   └── AttendanceReport.tsx
│   ├── invitations/
│   │   ├── InvitationForm.tsx
│   │   └── InvitationList.tsx
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Layout.tsx
│   ├── ProtectedRoute.tsx
│   └── ErrorBoundary.tsx
├── pages/
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── UsersPage.tsx
│   ├── AttendancePage.tsx
│   ├── SettingsPage.tsx
│   └── UnauthorizedPage.tsx
├── stores/
│   └── auth-store.ts
├── lib/
│   ├── api-client.ts
│   ├── api.ts
│   └── react-query.ts
├── hooks/
│   └── useApiError.ts
├── types/
│   └── index.ts
├── App.tsx
├── main.tsx
└── vite-env.d.ts
```

---

## Environment Variables

```bash
# .env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_APP_NAME=HRM SaaS
```

```bash
# .env.production
VITE_API_BASE_URL=https://api.hrmsaas.com
VITE_APP_NAME=HRM SaaS
```

---

## Production Deployment Checklist

1. **CORS Configuration**: Add your frontend domain to `CORS_ALLOWED_ORIGINS`
2. **HTTPS**: Use HTTPS in production
3. **Token Storage**: Consider using httpOnly cookies for tokens in production
4. **Subdomain Setup**: Configure wildcard subdomain in your DNS
5. **Environment Variables**: Securely manage environment variables
6. **Error Tracking**: Implement error tracking (Sentry, LogRocket)
7. **Analytics**: Add analytics (GA4, Mixpanel)
8. **Performance**: Implement lazy loading and code splitting
9. **SEO**: Add meta tags and Open Graph tags
10. **Testing**: Implement comprehensive testing

---

This completes the frontend implementation guide. Use this as a reference to build your HRM SaaS frontend.
