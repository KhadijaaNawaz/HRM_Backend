# Using x-tenant-id Header Instead of Host Header

Complete guide for using custom `x-tenant-id` header for tenant resolution.

---

## Why Use x-tenant-id Instead of Host Header?

| Aspect | Host Header | x-tenant-id Header |
|--------|-------------|-------------------|
| **CORS Issues** | Can cause conflicts | No conflicts |
| **Proxy/LB Friendly** | May not forward correctly | Always forwarded |
| **Explicit** | Implicit (from URL) | Explicit (custom header) |
| **Debugging** | Harder to debug | Easy to see and test |
| **Frontend Simplicity** | Must extract from URL | Just send header |

---

## How It Works Now

The middleware checks for tenant in this order:

```
1. x-tenant-id header      ← HIGHEST PRIORITY
   ├─ Accepts: "acme", "techcorp", etc.
   └─ Examples: from slug, domain, or ID

2. Host header              ← FALLBACK (original behavior)
   └─ Example: "acme.localhost"

3. ?tenant query param    ← LAST RESORT
   └─ Example: "?tenant=acme"
```

---

## Frontend Implementation

### Method 1: Using x-tenant-id Header (Recommended)

```typescript
// src/lib/api-client.ts
import axios from 'axios';

const API_BASE_URL = 'http://192.168.10.5:8000';

// Set default tenant (could come from localStorage, URL, etc.)
const DEFAULT_TENANT = 'acme';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
});

// Request interceptor - add x-tenant-id header
apiClient.interceptors.request.use((config) => {
  // Get tenant from various sources
  const tenant = getTenant();

  // Add x-tenant-id header instead of Host header
  if (config.headers) {
    config.headers['x-tenant-id'] = tenant;

    // Add auth token
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return config;
});

function getTenant(): string {
  // Priority 1: URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const urlTenant = urlParams.get('tenant');
  if (urlTenant) return urlTenant;

  // Priority 2: localStorage
  const storedTenant = localStorage.getItem('tenant');
  if (storedTenant) return storedTenant;

  // Priority 3: Extract from email (during login)
  const email = localStorage.getItem('user_email');
  if (email) {
    const domain = email.split('@')[1];
    if (domain) {
      const parts = domain.split('.');
      if (parts[0] && parts[0] !== 'gmail' && parts[0] !== 'yahoo') {
        return parts[0];  // e.g., "acme" from "acme.com"
      }
    }
  }

  // Default
  return DEFAULT_TENANT;
}
```

### Login with x-tenant-id:

```typescript
// Login service
export const authService = {
  async login(email: string, password: string) {
    // Extract tenant from email
    const tenant = email.split('@')[1]?.split('.')[0] || 'acme';

    // Store tenant for future requests
    localStorage.setItem('tenant', tenant);
    localStorage.setItem('user_email', email);

    // Make login request with x-tenant-id header
    const response = await apiClient.post('/api/v1/auth/login/', {
      email,
      password,
    });

    return response.data;
  },

  logout() {
    localStorage.removeItem('tenant');
    localStorage.removeItem('user_email');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }
};
```

---

## Postman Configuration

### Method 1: Using x-tenant-id Header

**Login Request:**

```
POST http://127.0.0.1:8000/api/v1/auth/login/

Headers:
┌──────────────────────────┬──────────────────────┐
│ Key                       │ Value                │
├──────────────────────────┼──────────────────────┤
│ Content-Type              │ application/json     │
│ x-tenant-id              │ acme                 │ ← NEW! Instead of Host
└──────────────────────────┴──────────────────────┘

Body (raw JSON):
{
  "email": "admin@acme.com",
  "password": "Admin123!"
}
```

**Or via Environment Variable:**
- Create/Update Postman environment
- Variable: `tenant_id` = `acme`
- In Headers: `x-tenant-id: {{tenant_id}}`

---

## Complete Frontend Example

### Auth Store with x-tenant-id

```typescript
// src/stores/auth-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  is_superuser: boolean;
  is_tenant_admin: boolean;
  roles: any[];
}

interface AuthState {
  user: User | null;
  tenant: string;
  isAuthenticated: boolean;
  setAuth: (tokens: any, user: User) => void;
  setTenant: (tenant: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tenant: 'acme',  // Default tenant
      isAuthenticated: false,

      setAuth: (tokens, user) => {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);
        set({ user, isAuthenticated: true });
      },

      setTenant: (tenant) => {
        localStorage.setItem('tenant', tenant);
        set({ tenant });
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // Keep tenant for convenience
        set({ user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        tenant: state.tenant,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helper hooks
export const useTenant = () => useAuthStore((state) => state.tenant);
export const useTenantId = () => useAuthStore((state) => state.tenant);
```

### API Client with x-tenant-id

```typescript
// src/lib/api-client.ts
import axios, { AxiosInstance } from 'axios';
import { useTenant } from '@/stores/auth-store';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.10.5:8000';

let apiClientInstance: AxiosInstance;

export function getApiClient() {
  if (!apiClientInstance) {
    apiClientInstance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      withCredentials: true,
    });

    // Request interceptor
    apiClientInstance.interceptors.request.use((config) => {
      // Get tenant from store (or localStorage)
      const tenant = localStorage.getItem('tenant') || 'acme';

      // Add x-tenant-id header
      config.headers['x-tenant-id'] = tenant;

      // Add auth token
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }

      return config;
    });

    // Response interceptor (token refresh)
    apiClientInstance.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Try refresh token
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const tenant = localStorage.getItem('tenant') || 'acme';
              const response = await axios.post(
                `${API_BASE_URL}/api/v1/auth/token/refresh/`,
                { refresh: refreshToken },
                {
                  headers: {
                    'Content-Type': 'application/json',
                    'x-tenant-id': tenant,
                  },
                }
              );

              const { access } = response.data;
              localStorage.setItem('access_token', access);

              // Retry original request
              error.config.headers['Authorization'] = `Bearer ${access}`;
              return axios.request(error.config);
            } catch (refreshError) {
              // Refresh failed, logout
              localStorage.clear();
              window.location.href = '/login';
            }
          }
        }
        throw error;
      }
    );
  }

  return apiClientInstance;
}

// Export singleton instance
export const apiClient = getApiClient();
```

### Login Page

```typescript
// src/pages/LoginPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth-store';
import { apiClient } from '@/lib/api-client';

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const setTenant = useAuthStore((state) => state.setTenant);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      // Extract tenant from email (e.g., admin@acme.com → acme)
      const domain = email.split('@')[1];
      const tenantSlug = domain ? domain.split('.')[0] : 'acme';

      // Store tenant
      setTenant(tenantSlug);

      // Make login request (apiClient auto-adds x-tenant-id header)
      const response = await apiClient.post('/api/v1/auth/login/', {
        email,
        password,
      });

      // Store auth data
      setAuth(response.data, response.data.user);

      // Redirect
      if (response.data.user.is_superuser) {
        navigate('/admin/tenants');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-center mb-6">Login</h2>

        {error && (
          <div className="bg-red-50 text-red-600 p-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@acme.com"
              className="w-full px-3 py-2 border rounded"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Tenant will be auto-detected from email domain
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="•••••••••"
              className="w-full px-3 py-2 border rounded"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Sign In
          </button>
        </form>

        <div className="mt-4 text-sm text-gray-600">
          <p>Tenant ID will be sent via <code class="bg-gray-100 px-1 rounded">x-tenant-id</code> header</p>
        </div>
      </div>
    </div>
  );
}
```

---

## Test with curl

```bash
# With x-tenant-id header (NEW METHOD)
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "x-tenant-id: acme" \
  -d '{"email":"admin@acme.com","password":"Admin123!"}'

# With Host header (ORIGINAL METHOD - still works)
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "Host: acme.localhost" \
  -d '{"email":"admin@acme.com","password":"Admin123!"}'

# With query parameter (FALLBACK)
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login/?tenant=acme" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acme.com","password":"Admin123!"}'
```

---

## Axios Configuration for x-tenant-id

```typescript
// vite.config.ts - Add proxy for development
import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Get tenant from localStorage
            const tenant = req.headers['referer']
              ? new URL(req.headers['referer']).searchParams.get('tenant') || 'acme'
              : 'acme';

            // Add x-tenant-id header to proxied request
            proxyReq.setHeader('x-tenant-id', tenant);
          });
        },
      },
    },
  },
});
```

---

## React Query / TanStack Query with x-tenant-id

```typescript
// src/lib/api-services.ts
import { getApiClient } from './api-client';

export const authService = {
  async login(email: string, password: string) {
    const apiClient = getApiClient();

    // apiClient will auto-add x-tenant-id header
    const response = await apiClient.post('/api/v1/auth/login/', {
      email,
      password,
    });

    return response.data;
  },

  async getCurrentUser() {
    const apiClient = getApiClient();
    const response = await apiClient.get('/api/v1/auth/me/');
    return response.data;
  },

  async logout() {
    const apiClient = getApiClient();
    await apiClient.post('/api/v1/auth/logout/', {
      refresh: localStorage.getItem('refresh_token'),
    });
  },
};
```

---

## Summary: Host Header vs x-tenant-id

### Before (Using Host Header)

```typescript
fetch('http://192.168.10.5:8000/api/v1/auth/login/', {
  headers: {
    'Host': 'acme.localhost'  // Required for tenant resolution
  }
});
```

### After (Using x-tenant-id Header)

```typescript
fetch('http://192.168.10.5:8000/api/v1/auth/login/', {
  headers: {
    'x-tenant-id': 'acme'  // Clear, explicit, no CORS issues!
  }
});
```

---

## Benefits of x-tenant-id

✅ **No CORS Issues** - Custom header doesn't trigger preflight like Host might
✅ **Proxy Friendly** - Works better with Nginx/Apache reverse proxies
✅ **Explicit** - Clear what tenant is being requested
✅ **Flexible** - Can be stored in localStorage, URL param, or derived from email
✅ **Debugging** - Easy to see in browser DevTools

---

## Restart Server Required

After updating the middleware, **restart Django server**:

```bash
cd F:\work\neuroceans\hrm_saas
python manage.py runserver 0.0.0.0:8000
```

Now your API supports three methods of tenant resolution:

1. **x-tenant-id header** (recommended) - `x-tenant-id: acme`
2. **Host header** (original) - `Host: acme.localhost`
3. **Query parameter** (fallback) - `?tenant=acme`
