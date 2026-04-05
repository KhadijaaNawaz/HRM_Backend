# How Frontend Knows the Tenant (Host Header)

Complete guide on how frontend determines which tenant to use for API requests.

---

## The Problem

Frontend needs to send `Host: acme.localhost` in API requests, but **how does it know** to use "acme" and not "techcorp" or something else?

---

## Solution Options

### Option 1: Extract from URL Subdomain (Recommended for Production)

**How it works:**
- User accesses: `http://acme.localhost:3000`
- Frontend extracts "acme" from the hostname
- Uses it for all API requests

```typescript
// Extract tenant from current URL
const getTenantFromUrl = (): string => {
  const hostname = window.location.hostname;

  // acme.localhost:3000 → ["acme", "localhost", "3000"]
  const parts = hostname.split('.');

  // Extract subdomain (first part)
  const subdomain = parts[0];  // "acme"

  return subdomain;
};

// Use in API calls
const tenant = getTenantFromUrl();  // "acme"
const apiUrl = 'http://192.168.10.5:8000';

fetch(`${apiUrl}/api/v1/auth/login/`, {
  headers: {
    'Host': `${tenant}.localhost`  // "acme.localhost"
  },
  body: JSON.stringify({ email, password })
});
```

**Setup required:**
```bash
# Add to hosts file
127.0.0.1  acme.localhost
127.0.0.1  techcorp.localhost
```

**URLs users access:**
- Acme: `http://acme.localhost:3000`
- TechCorp: `http://techcorp.localhost:3000`

---

### Option 2: Query Parameter (Good for Development)

**How it works:**
- User accesses: `http://192.168.10.5:8080/login?tenant=acme`
- Frontend reads tenant from URL parameter
- Stores it for subsequent requests

```typescript
// Get tenant from URL parameter
const getTenantFromUrl = (): string => {
  const urlParams = new URLSearchParams(window.location.search);
  const tenant = urlParams.get('tenant');

  if (tenant) {
    // Store for subsequent requests
    localStorage.setItem('tenant', tenant);
    return tenant;
  }

  // Fallback to stored value
  return localStorage.getItem('tenant') || 'acme';
};

// Use in API calls
const tenant = getTenantFromUrl();

fetch(`${apiUrl}/api/v1/auth/login/`, {
  headers: {
    'Host': `${tenant}.localhost`
  }
});
```

**URLs users access:**
- `http://192.168.10.5:8080/login?tenant=acme`
- `http://192.168.10.5:8080/login?tenant=techcorp`

---

### Option 3: Extract from User's Email (During Login)

**How it works:**
- User enters email: `admin@acme.com`
- Frontend extracts "acme" from email domain
- Uses it for login request, then stores it

```typescript
// Extract tenant from email during login
const extractTenantFromEmail = (email: string): string => {
  const domain = email.split('@')[1];  // "acme.com"
  const tenant = domain.split('.')[0];  // "acme"

  return tenant;
};

// During login
const handleLogin = async (email: string, password: string) => {
  const tenant = extractTenantFromEmail(email);  // "acme"

  // Store for subsequent requests
  localStorage.setItem('tenant', tenant);

  fetch(`${apiUrl}/api/v1/auth/login/`, {
    headers: {
      'Host': `${tenant}.localhost`
    },
    body: JSON.stringify({ email, password })
  });
};
```

**Login form:**
```typescript
<input
  type="email"
  placeholder="admin@acme.com"
  onChange={(e) => {
    // Auto-detect tenant from email
    const tenant = extractTenantFromEmail(e.target.value);
    localStorage.setItem('tenant', tenant);
  }}
/>
```

---

### Option 4: Tenant Selection Page (Common SaaS Pattern)

**How it works:**
- Show tenant selection page before login
- User selects their organization
- Store it and redirect to login

```typescript
// Tenant selection page
function TenantSelectionPage() {
  const tenants = [
    { slug: 'acme', name: 'Acme Corporation', logo: '/logos/acme.png' },
    { slug: 'techcorp', name: 'TechCorp Inc.', logo: '/logos/techcorp.png' },
  ];

  const selectTenant = (tenant: any) => {
    localStorage.setItem('tenant', tenant.slug);
    window.location.href = `/login`;
  };

  return (
    <div>
      <h1>Select your organization</h1>
      {tenants.map(tenant => (
        <div
          key={tenant.slug}
          onClick={() => selectTenant(tenant)}
          className="tenant-card"
        >
          <img src={tenant.logo} alt={tenant.name} />
          <h3>{tenant.name}</h3>
        </div>
      ))}
    </div>
  );
}
```

**Then in login:**
```typescript
const tenant = localStorage.getItem('tenant');  // "acme"

fetch(`${apiUrl}/api/v1/auth/login/`, {
  headers: {
    'Host': `${tenant}.localhost`
  }
});
```

---

### Option 5: Domain-Based Routing (Production Best Practice)

**How it works:**
- Each tenant has their own domain (e.g., `acme.hrmsaas.com`)
- Frontend automatically extracts tenant from domain
- No user action needed

```typescript
// Works for both subdomains and custom domains
const getTenantFromDomain = (): string => {
  const hostname = window.location.hostname;

  // Subdomain: acme.hrmsaas.com → "acme"
  if (hostname.includes('.hrmsaas.com')) {
    const parts = hostname.split('.');
    return parts[0];
  }

  // Custom domain: acme-corp.com → "acme"
  // (Requires backend mapping)

  return localStorage.getItem('tenant') || 'acme';
};
```

---

### Option 6: Hybrid Approach (Most Flexible)

Combines multiple methods with fallbacks:

```typescript
// tenant-utils.ts

export type TenantSource = 'url' | 'param' | 'storage' | 'email' | 'default';

interface TenantInfo {
  slug: string;
  source: TenantSource;
}

/**
 * Get tenant with multiple fallback strategies
 */
export function getTenantInfo(): TenantInfo {
  // 1. Try URL subdomain (highest priority for production)
  const hostname = window.location.hostname;
  if (hostname.includes('.localhost') || hostname.includes('.hrmsaas.com')) {
    const parts = hostname.split('.');
    const slug = parts[0];
    if (slug && slug !== 'www' && slug !== 'app') {
      return { slug, source: 'url' };
    }
  }

  // 2. Try URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const tenantParam = urlParams.get('tenant');
  if (tenantParam) {
    return { slug: tenantParam, source: 'param' };
  }

  // 3. Try localStorage (previous selection)
  const storedTenant = localStorage.getItem('tenant');
  if (storedTenant) {
    return { slug: storedTenant, source: 'storage' };
  }

  // 4. Default fallback
  return { slug: 'acme', source: 'default' };
}

/**
 * Get the Host header value for API requests
 */
export function getTenantHost(): string {
  const { slug } = getTenantInfo();
  return `${slug}.localhost`;
}

/**
 * Save tenant for future use
 */
export function setTenant(slug: string): void {
  localStorage.setItem('tenant', slug);
}

/**
 * Extract tenant from email address
 */
export function extractTenantFromEmail(email: string): string | null {
  if (!email || !email.includes('@')) return null;

  const domain = email.split('@')[1];

  // Handle common patterns:
  // user@acme.com → acme
  // user@mail.acme.com → acme
  // user@acme.hrmsaas.com → acme

  // Extract from first part of domain before common patterns
  const parts = domain.split('.');

  // Pattern: user@acme.com
  if (parts.length === 2) {
    return parts[0];
  }

  // Pattern: user@mail.acme.com
  if (parts[1] === 'mail' && parts.length === 3) {
    return parts[1]; // Actually 'acme' in this case
  }

  // Pattern: user@acme.hrmsaas.com
  if (parts[parts.length - 1] === 'com' && parts.length >= 2) {
    const possibleTenant = parts[parts.length - 2];
    if (possibleTenant !== 'hrmsaas') {
      return possibleTenant;
    }
  }

  return null;
}
```

---

## Complete Implementation Example

### Axios Instance with Auto Tenant Detection

```typescript
// lib/api-client.ts
import axios from 'axios';
import { getTenantHost, setTenant, extractTenantFromEmail } from './tenant-utils';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://192.168.10.5:8000';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
});

// Request interceptor - add tenant host header
apiClient.interceptors.request.use((config) => {
  // Get tenant host (auto-detected)
  const tenantHost = getTenantHost();

  // Add Host header for tenant resolution
  config.headers['Host'] = tenantHost;

  // Add auth token if available
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
}, (error) => {
  return Promise.reject(error);
});

// Login service with tenant extraction
export const authService = {
  async login(email: string, password: string) {
    // Extract tenant from email for first request
    const tenant = extractTenantFromEmail(email);

    if (tenant) {
      // Store tenant for subsequent requests
      setTenant(tenant);
    }

    const response = await apiClient.post('/api/v1/auth/login/', {
      email,
      password,
    });

    // Verify tenant from response
    if (response.data.user?.organization) {
      setTenant(response.data.user.organization.slug);
    }

    return response.data;
  }
};
```

---

## React Context for Tenant

```typescript
// contexts/TenantContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getTenantInfo, setTenant as saveTenant, getTenantHost } from '@/lib/tenant-utils';

interface TenantContextValue {
  tenant: string;
  tenantHost: string;
  setTenant: (slug: string) => void;
  isTenantSet: boolean;
}

const TenantContext = createContext<TenantContextValue | undefined>(undefined);

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenantState] = useState<string>('acme');
  const [isTenantSet, setIsTenantSet] = useState(false);

  useEffect(() => {
    // Auto-detect tenant on mount
    const { slug, source } = getTenantInfo();
    setTenantState(slug);
    setIsTenantSet(source !== 'default');
  }, []);

  const setTenant = (slug: string) => {
    saveTenant(slug);
    setTenantState(slug);
    setIsTenantSet(true);
  };

  const tenantHost = getTenantHost();

  return (
    <TenantContext.Provider value={{ tenant, tenantHost, setTenant, isTenantSet }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within TenantProvider');
  }
  return context;
}
```

---

## Usage in Components

### Login Page with Auto Tenant Detection

```typescript
import { useState } from 'react';
import { useTenant } from '@/contexts/TenantContext';
import { authService } from '@/lib/api-service';

export default function LoginPage() {
  const { tenantHost } = useTenant();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // authService will auto-extract tenant from email
      const response = await authService.login(email, password);

      // Store tokens and redirect
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);

      // Redirect based on user role
      if (response.user.is_superuser) {
        window.location.href = '/admin/tenants';
      } else {
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  // For debugging - show current tenant
  console.log('Current tenant host:', tenantHost);

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="admin@acme.com"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit">Login</button>
      <p>Logging in to tenant: {tenantHost}</p>
    </form>
  );
}
```

---

## Development vs Production

### Development (Localhost)

```typescript
// Development - Multiple approaches

// Option A: Subdomain with hosts file
// URL: http://acme.localhost:3000
const tenant = window.location.hostname.split('.')[0];  // "acme"

// Option B: Query parameter
// URL: http://192.168.10.5:8080?tenant=acme
const tenant = new URLSearchParams(location.search).get('tenant');

// Option C: Stored from previous selection
const tenant = localStorage.getItem('tenant') || 'acme';
```

### Production

```typescript
// Production - Domain-based

// URL: http://acme.hrmsaas.com
const hostname = window.location.hostname;  // "acme.hrmsaas.com"
const tenant = hostname.split('.')[0];  // "acme"

// Works for all tenants automatically:
// acme.hrmsaas.com → acme
// techcorp.hrmsaas.com → techcorp
// startup.hrmsaas.com → startup
```

---

## URL Patterns Summary

| Approach | Example URL | How Tenant is Determined |
|-----------|-------------|--------------------------|
| **Subdomain** | `http://acme.localhost:3000` | Extract from hostname |
| **Custom Domain** | `http://acme.hrmsaas.com` | Extract from hostname |
| **Query Param** | `http://192.168.10.5:8080?tenant=acme` | Read from URL param |
| **Selection Page** | `/select-tenant` → `/login` | Stored from selection |
| **Email Domain** | `user@acme.com` | Extract from email |

---

## Recommended Setup

### For Development (Quick Start)

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    host: true,  // Listen on all interfaces
  }
})

// Access via: http://acme.localhost:3000
// Tenant auto-extracted from URL
```

Add to `C:\Windows\System32\drivers\etc\hosts`:
```
127.0.0.1  acme.localhost
127.0.0.1  techcorp.localhost
```

### For Production

```
DNS Configuration:
acme.hrmsaas.com     → Frontend server
techcorp.hrmsaas.com → Frontend server

Nginx routes both to same frontend app, which extracts tenant from URL.
```

---

## Quick Test

```typescript
// Add this to your App.tsx for debugging
useEffect(() => {
  const hostname = window.location.hostname;
  const tenant = hostname.split('.')[0];
  const tenantHost = `${tenant}.localhost`;

  console.log('Hostname:', hostname);
  console.log('Tenant:', tenant);
  console.log('Tenant Host:', tenantHost);

  // This will show you what's being used
}, []);
```

---

## Summary

The frontend knows the tenant through these methods:

1. **Extract from URL** (Production) - Extract subdomain from current URL
2. **Query Parameter** (Development) - Read `?tenant=acme` from URL
3. **Email Extraction** - Extract from email during login
4. **Selection Page** - User selects from list
5. **Stored Value** - Previously selected tenant from localStorage

**Most Common:** Extract from URL subdomain (`acme.localhost` → `acme`)
