# CORS Error Troubleshooting Guide

Complete guide to fixing CORS errors in HRM SaaS frontend integration.

---

## What is CORS Error?

**CORS (Cross-Origin Resource Sharing)** errors occur when:

```
Frontend URL: http://localhost:3000
Backend URL:  http://127.0.0.1:8000
              ↑ Different origins = CORS requirement
```

**Typical Error Message:**
```
Access to fetch at 'http://127.0.0.1:8000/api/v1/auth/login/'
from origin 'http://localhost:3000' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

---

## Common Causes & Solutions

### 1. Frontend URL Not in Allowed Origins

**Problem:** Frontend URL (e.g., `localhost:5173` for Vite) is not in `CORS_ALLOWED_ORIGINS`

**Solution A: Update .env file**
```bash
# .env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

**Solution B: Allow all origins (DEV ONLY!)**
```python
# config/settings.py
CORS_ALLOW_ALL_ORIGINS = True  # ONLY FOR DEVELOPMENT!
```

---

### 2. Subdomain Not Allowed (Multi-Tenancy Issue)

**Problem:** Using subdomain like `acme.localhost:3000` but only `localhost:3000` is allowed

**Solution:** Add wildcard or specific subdomains

```python
# config/settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://acme.localhost:3000',
    'http://*.localhost:3000',  # This won't work directly
]

# For wildcard subdomains in development:
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https?://(\w+\.)?localhost:3000$',  # Matches acme.localhost:3000, test.localhost:3000, etc.
]
```

---

### 3. Credentials Not Allowed

**Problem:** Sending cookies/auth headers but `CORS_ALLOW_CREDENTIALS` is False

**Solution:**
```python
# config/settings.py
CORS_ALLOW_CREDENTIALS = True  # Already set in your config
```

**Frontend must also include:**
```typescript
// axios/fetch must include credentials
axios.defaults.withCredentials = true; // For axios

// OR for fetch
fetch(url, {
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' }
});
```

---

### 4. Host Header Issue (Multi-Tenancy Specific)

**Problem:** The `Host` header for tenant resolution conflicts with CORS

**Issue:** When frontend sets `Host: acme.localhost`, browser's preflight OPTIONS request may fail.

**Solution A: Use different approach for tenant resolution**

```typescript
// Instead of relying solely on Host header, pass tenant info in URL
// Backend: Update middleware to check both Host header AND query parameter

// Frontend:
const response = await axios.get('http://127.0.0.1:8000/api/v1/auth/me/', {
  headers: {
    'X-Tenant-Host': 'acme.localhost',  // Custom header instead of Host
    'Authorization': `Bearer ${token}`,
  }
});
```

**Solution B: Proxy through frontend dev server**

```javascript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Add tenant subdomain to Host header
            const hostname = req.headers.host; // e.g., acme.localhost:5173
            const tenant = hostname.split('.')[0]; // extract 'acme'
            proxyReq.setHeader('Host', `${tenant}.localhost`);
          });
        }
      }
    }
  }
});
```

**Solution C: Nginx/Proxy in production**

```nginx
# Nginx configuration
server {
    server_name *.localhost;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

---

### 5. Preflight OPTIONS Request Failing

**Problem:** Browser sends OPTIONS request before POST/PUT/DELETE, but it fails

**Solution:** Ensure CORS middleware handles OPTIONS

```python
# config/settings.py - MIDDLEWARE order matters!
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',  # MUST be first
    'corsheaders.middleware.CorsMiddleware',               # MUST be early
    'django.middleware.security.SecurityMiddleware',
    # ... rest of middleware
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'host',  # Important for multi-tenancy!
]
```

---

## Complete CORS Configuration

### For Development (All Fixes)

```python
# config/settings.py
INSTALLED_APPS = [
    # ...
    'corsheaders',
    # ...
]

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # As early as possible
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ...
]

# CORS Configuration for Development
CORS_ALLOW_ALL_ORIGINS = True  # ONLY FOR DEVELOPMENT!
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# OR for Production:
CORS_ALLOWED_ORIGINS = [
    'https://acme.yourdomain.com',
    'https://techcorp.yourdomain.com',
    'https://app.yourdomain.com',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'host',  # Critical for tenant resolution
]
```

---

## Frontend Configuration Examples

### React with Vite

```typescript
// src/lib/api-client.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,  // Important for CORS
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add tenant host
apiClient.interceptors.request.use((config) => {
  // Get tenant from current URL subdomain
  const hostname = window.location.hostname;

  // For development: extract subdomain from acme.localhost:5173
  if (hostname.includes('.localhost')) {
    const tenant = hostname.split('.')[0];
    config.headers['Host'] = `${tenant}.localhost`;
  }

  // Add auth token
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});
```

### Vite Proxy Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3000,
    host: true,  // Listen on all addresses
  },
})
```

### Environment Variables

```bash
# .env.development
VITE_API_BASE_URL=http://127.0.0.1:8000

# .env.production
VITE_API_BASE_URL=https://api.hrmsaas.com
```

---

## Testing CORS Setup

### 1. Test Direct API Call (No CORS)

```bash
# This should work - testing backend directly
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "Host: acme.localhost" \
  -d '{"email":"admin@acme.com","password":"Admin123!"}'
```

### 2. Test CORS Preflight

```bash
# This tests the OPTIONS request (what browser sends first)
curl -X OPTIONS http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,host,authorization" \
  -v
```

**Expected Response Headers:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: POST, OPTIONS
Access-Control-Allow-Headers: content-type, host, authorization
Access-Control-Allow-Credentials: true
```

### 3. Test from Browser Console

```javascript
// Open browser console on http://localhost:3000
fetch('http://127.0.0.1:8000/api/v1/auth/me/', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

---

## Production CORS Setup

### Using Same Domain (Recommended)

```
Frontend: https://acme.yourdomain.com
Backend:  https://acme.yourdomain.com/api/*
                      ↑ Same origin = No CORS issues!
```

### Nginx Configuration

```nginx
server {
    server_name *.yourdomain.com;

    # Frontend (React/Vue/Angular build)
    location / {
        root /var/www/hrm-saas/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Production Settings

```python
# config/settings.py (production)
DEBUG = False
ALLOWED_HOSTS = ['.yourdomain.com', 'yourdomain.com']

CORS_ALLOWED_ORIGINS = [
    'https://*.yourdomain.com',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://(\w+\.)*yourdomain\.com$',
]
```

---

## Quick Fix Checklist

✅ **Backend:**
- [ ] `corsheaders` in `INSTALLED_APPS`
- [ ] `CorsMiddleware` near top of `MIDDLEWARE`
- [ ] Frontend URL in `CORS_ALLOWED_ORIGINS`
- [ ] `CORS_ALLOW_CREDENTIALS = True`
- [ ] `Host` in `CORS_ALLOW_HEADERS`

✅ **Frontend:**
- [ ] `withCredentials: true` for axios
- [ ] API calls include `Host` header for tenant
- [ ] Token sent in `Authorization` header

✅ **Development:**
- [ ] Both backend and server running
- [ ] Correct ports in URLs
- [ ] Browser not caching old responses (try Incognito mode)

---

## Debug Commands

```bash
# Check Django settings
python manage.py shell -c "from django.conf import settings; print(settings.CORS_ALLOWED_ORIGINS)"

# Test backend is running
curl http://127.0.0.1:8000/api/v1/auth/me/

# Check what origins are allowed
curl -I http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Origin: http://localhost:3000"
```

---

## Still Having Issues?

1. **Check browser console** for exact error message
2. **Check Network tab** to see which request is failing
3. **Verify backend is running** on correct port
4. **Try Incognito/Private mode** to rule out caching
5. **Check Django logs** for any error messages
6. **Verify tenant exists** and domain is configured correctly

---

## Summary: Superuser Storage & CORS

### Superuser Storage
- **Table:** `users` table within tenant schema (e.g., `acme.users`)
- **Field:** `is_superuser` boolean field on User model
- **Location:** Created in specific tenant schema, but has platform-wide access

### CORS Errors
- **Root Cause:** Browser security blocks cross-origin requests without proper headers
- **Quick Fix:** Add frontend URL to `CORS_ALLOWED_ORIGINS`
- **Long-term Fix:** Use same domain with Nginx proxy in production
