# Multi-Tenant Login Flow - Superuser vs Tenant Users

## Key Concept: ALL Logins Go Through Tenant Subdomain

In this HRM SaaS system, **there is no separate "superuser login URL"**.

Both superusers AND regular tenant users login through the **same tenant subdomain URL**.

---

## Login URLs

### Tenant-Based Login URLs

| User Type | Tenant | Login URL |
|-----------|--------|-----------|
| **Superuser** | Acme Corp | `http://acme.localhost:8000/api/v1/auth/login/` |
| **Tenant Admin** | Acme Corp | `http://acme.localhost:8000/api/v1/auth/login/` |
| **HR User** | Acme Corp | `http://acme.localhost:8000/api/v1/auth/login/` |
| **Employee** | Acme Corp | `http://acme.localhost:8000/api/v1/auth/login/` |
| **Superuser** | TechCorp | `http://techcorp.localhost:8000/api/v1/auth/login/` |
| **Any User** | TechCorp | `http://techcorp.localhost:8000/api/v1/auth/login/` |

**Key Point:** Everyone uses the **same login endpoint** on their tenant's subdomain.

---

## How It Works

### 1. Frontend Makes Login Request

```typescript
// Frontend URL: http://acme.localhost:3000/login
// API Request:
const response = await fetch('http://127.0.0.1:8000/api/v1/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Host': 'acme.localhost',  // ← CRITICAL: Tenant identification
  },
  body: JSON.stringify({
    email: 'admin@acme.com',  // or 'superadmin@hrmsaas.com'
    password: 'Admin123!'
  })
});
```

### 2. Backend Processes Login

```python
# Django Tenant Middleware Flow:

1. Request arrives at: http://127.0.0.1:8000/api/v1/auth/login/

2. TenantMainMiddleware intercepts:
   - Reads Host header: "acme.localhost"
   - Looks up Domain table: finds acme.localhost → Organization "acme"
   - Switches to schema: "acme"

3. LoginView executes in "acme" schema:
   - Queries users table in acme schema
   - Finds user by email
   - Verifies password
   - Returns user data with role info

4. Response includes:
   - access_token (JWT)
   - refresh_token
   - user: {
       email: "admin@acme.com",
       is_superuser: false,      ← Boolean flag
       is_tenant_admin: true,    ← Boolean flag
       roles: [{ name: "Admin" }]
     }
```

---

## User Storage & Access

### Where Users Live

```
PostgreSQL Database: hrm_saas
│
├── public schema
│   ├── organizations (all tenants)
│   └── domains (all tenant domains)
│
├── acme schema (acme.localhost)
│   └── users
│       ├── admin@acme.com          (is_tenant_admin: true)
│       ├── hr@acme.com             (roles: [HR])
│       ├── employee@acme.com       (roles: [Employee])
│       └── superadmin@hrmsaas.com  (is_superuser: true) ← Also here!
│
├── techcorp schema (techcorp.localhost)
│   └── users
│       ├── admin@techcorp.com
│       └── employee@techcorp.com
│
└── other tenants...
```

### Important Points:

1. **Superuser exists in a tenant schema** - Not in public schema
2. **Same email can exist in different tenants** - They're different users
3. **is_superuser flag gives platform-wide access** - But user still lives in one tenant

---

## Permission Resolution

### Backend Checks (Using Tenant Host Header)

```python
# In permissions.py or views.py:

def has_permission(request, view):
    user = request.user

    # 1. Check if superuser (platform admin)
    if user.is_superuser:
        return True  # Full access to ALL tenants, ALL APIs

    # 2. Check if tenant admin (organization admin)
    if user.is_tenant_admin:
        return True  # Full access within THIS tenant

    # 3. Check roles
    if user.roles.filter(name='HR').exists():
        return True  # HR permissions

    if user.roles.filter(name='Employee').exists():
        return True  # Employee permissions (self-only)

    return False
```

### Frontend Role Checks

```typescript
// After login, store user data:
const user = {
  email: 'admin@acme.com',
  is_superuser: false,
  is_tenant_admin: true,
  roles: [{ name: 'Admin', description: '...' }]
};

// Check permissions in UI:
const canManageUsers = user.is_tenant_admin ||
                       user.is_superuser ||
                       user.roles.some(r => r.name === 'HR');

const canAccessAdminPanel = user.is_superuser;  // Only superuser
```

---

## Complete Login Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                 │
│  URL: http://acme.localhost:3000/login                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ POST /api/v1/auth/login/
                           │ Headers: Host: acme.localhost
                           │ Body: { email, password }
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                 │
│  URL: http://127.0.0.1:8000/api/v1/auth/login/                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              TenantMainMiddleware                               │
│  1. Read Host header: "acme.localhost"                         │
│  2. Query domains table: acme.localhost → org_id               │
│  3. Set search_path to: "acme" schema                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LoginView (in acme schema)                    │
│  1. Query: SELECT * FROM users WHERE email = ?                │
│  2. Verify password                                            │
│  3. Get user data:                                             │
│     - is_superuser: boolean                                    │
│     - is_tenant_admin: boolean                                 │
│     - roles: [...]                                             │
│  4. Generate JWT tokens                                        │
│  5. Return user + tokens                                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RESPONSE                                   │
│  {                                                              │
│    "access": "eyJhbGciOiJIUzI1NiIs...",                        │
│    "refresh": "eyJhbGciOiJIUzI1NiIs...",                       │
│    "user": {                                                   │
│      "email": "admin@acme.com",                                │
│      "is_superuser": false,    ← Determined by DB field         │
│      "is_tenant_admin": true,  ← Determined by DB field         │
│      "roles": [                                                │
│        { "name": "Admin", ... }                                │
│      ]                                                         │
│    }                                                           │
│  }                                                             │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (stores user)                        │
│  localStorage.setItem('access_token', access)                  │
│  localStorage.setItem('user', JSON.stringify(user))            │
│                                                                 │
│  Route based on roles:                                          │
│  - is_superuser: true  → Can access /admin/*                   │
│  - is_tenant_admin: true → Can access /users, /roles, etc.    │
│  - roles includes HR    → Can access /users, /attendance       │
│  - roles includes Employee → Can access own attendance         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend Tenant Detection

### Method 1: Extract from URL (Recommended)

```typescript
// Get tenant from current URL
const getTenantFromUrl = (): string => {
  const hostname = window.location.hostname;

  // Development: acme.localhost:3000 → "acme"
  if (hostname.includes('.localhost')) {
    return hostname.split('.')[0];
  }

  // Production: acme.hrmsaas.com → "acme"
  const parts = hostname.split('.');
  if (parts.length >= 2) {
    return parts[0];
  }

  return 'default';
};

// Use for API calls
const tenant = getTenantFromUrl(); // "acme"
const apiUrl = 'http://192.168.10.5:8000';

fetch(`${apiUrl}/api/v1/auth/login/`, {
  headers: {
    'Host': `${tenant}.localhost`,  // "acme.localhost"
  },
  body: JSON.stringify({ email, password })
});
```

### Method 2: Store in Login Response

```typescript
// After login, store tenant info
const loginResponse = await fetch('/api/v1/auth/login/', ...);
const data = await loginResponse.json();

// Extract tenant from user's organization
const tenantInfo = {
  slug: data.user.organization?.slug,  // "acme"
  name: data.user.organization?.name,  // "Acme Corporation"
};

localStorage.setItem('tenant', JSON.stringify(tenantInfo));
```

---

## Superuser vs Regular User Access

### Superuser Login Flow

```typescript
// 1. User visits: http://acme.localhost:3000/login
// 2. Enters: superadmin@hrmsaas.com / SuperAdmin123!
// 3. API call with: Host: acme.localhost
// 4. Response includes:
{
  "user": {
    "email": "superadmin@hrmsaas.com",
    "is_superuser": true,  ← True
    "is_tenant_admin": true,  ← Also true (superusers are tenant admins too)
    "roles": []
  }
}

// 5. Frontend checks:
if (user.is_superuser) {
  // Show admin menu items
  // Can access /admin/tenants
  // Can manage all tenants
}
```

### Regular User Login Flow

```typescript
// 1. User visits: http://acme.localhost:3000/login
// 2. Enters: employee@acme.com / Employee123!
// 3. API call with: Host: acme.localhost
// 4. Response includes:
{
  "user": {
    "email": "employee@acme.com",
    "is_superuser": false,  ← False
    "is_tenant_admin": false,  ← False
    "roles": [
      { "name": "Employee", ... }
    ]
  }
}

// 5. Frontend checks:
if (user.is_superuser) {
  // Skip admin features
} else if (user.is_tenant_admin) {
  // Show admin features
} else if (userHasRole('HR')) {
  // Show HR features
} else {
  // Show employee features only
}
```

---

## Subdomain Setup for Development

### Option 1: Add to Hosts File

```bash
# Windows: C:\Windows\System32\drivers\etc\hosts
# Linux/Mac: /etc/hosts

127.0.0.1  acme.localhost
127.0.0.1  techcorp.localhost
127.0.0.1  startup.localhost
```

Then access frontend at:
- `http://acme.localhost:3000`
- `http://techcorp.localhost:3000`

### Option 2: Use IP-Based URL (Network Access)

```
http://192.168.10.5:8080?tenant=acme
```

Backend reads tenant from query parameter (requires middleware update):

```python
# tenants/middleware.py (custom enhancement)
def get_tenant_from_request(request):
    # Try Host header first
    host = request.META.get('HTTP_HOST')

    # Fallback to query parameter
    if not host or 'localhost' in host:
        tenant_slug = request.GET.get('tenant')
        if tenant_slug:
            # Look up tenant and set schema
            tenant = Organization.objects.get(slug=tenant_slug)
            return tenant
```

---

## API Endpoint Summary

### Login Endpoint (Same for Everyone)

```
URL: http://192.168.10.5:8000/api/v1/auth/login/
Method: POST
Headers:
  Content-Type: application/json
  Host: acme.localhost  ← Determines which tenant schema to use

Body:
{
  "email": "user@email.com",
  "password": "password"
}

Response:
{
  "access": "jwt_token",
  "refresh": "refresh_token",
  "user": {
    "id": "uuid",
    "email": "user@email.com",
    "is_superuser": boolean,    ← Determines if platform admin
    "is_tenant_admin": boolean, ← Determines if org admin
    "roles": [...],              ← Determines HR/Employee
    "organization": {
      "slug": "acme",           ← Current tenant
      "name": "Acme Corporation"
    }
  }
}
```

---

## Frontend Implementation

### Complete Login Component

```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth-store';

// Get tenant from current URL
const getTenantHost = (): string => {
  const hostname = window.location.hostname;

  if (hostname.includes('.localhost')) {
    return hostname;  // Return "acme.localhost"
  }

  // For production or IP-based access
  const tenantSlug = localStorage.getItem('tenant_slug') || 'acme';
  return `${tenantSlug}.localhost`;
};

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      // Get tenant host for current URL
      const tenantHost = getTenantHost();
      const apiUrl = 'http://192.168.10.5:8000';

      const response = await fetch(`${apiUrl}/api/v1/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Host': tenantHost,  // Critical: identifies tenant
        },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();

      // Store auth data
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      localStorage.setItem('tenant_host', tenantHost);

      // Update auth store
      setAuth(data, data.user);

      // Navigate based on user role
      if (data.user.is_superuser) {
        navigate('/admin/tenants');
      } else if (data.user.is_tenant_admin) {
        navigate('/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError('Invalid email or password');
    }
  };

  return (
    <form onSubmit={handleLogin}>
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
      <button type="submit">Login</button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}
```

---

## Summary

| Question | Answer |
|----------|--------|
| **Where do users login?** | Through their tenant's subdomain URL (e.g., `acme.localhost`) |
| **Same URL for all user types?** | Yes! Superuser, Admin, HR, Employee all use the same login endpoint |
| **How does backend know the tenant?** | From the `Host` header in the request |
| **How does backend know user type?** | From `is_superuser`, `is_tenant_admin` flags and `roles` in database |
| **Where is superuser stored?** | In the `users` table within a tenant schema (e.g., `acme.users`) |
| **Can superuser access all tenants?** | Yes, but must login through a tenant URL first |
| **Frontend: How to determine permissions?** | Check `is_superuser`, `is_tenant_admin`, and `roles` from login response |

---

## Quick Reference

### Login URLs for Different Tenants

```
Acme Corp:     http://acme.localhost:3000/login
TechCorp:       http://techcorp.localhost:3000/login
Startup Inc:    http://startup.localhost:3000/login
```

### All call the same backend API

```
POST http://192.168.10.5:8000/api/v1/auth/login/
Host: [tenant].localhost
```

### Backend determines:
1. **Which tenant** → From `Host` header
2. **Which user** → From `email` and `password`
3. **What permissions** → From `is_superuser`, `is_tenant_admin`, `roles` in database
