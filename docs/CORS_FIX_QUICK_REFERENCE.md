# CORS Fix - Quick Reference

## Changes Made

### 1. Updated `.env` file
```bash
# Added your frontend URL to CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://192.168.10.5:8080,http://localhost:8080,http://127.0.0.1:8080

# Added your IP to ALLOWED_HOSTS
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.10.5
```

### 2. Updated `config/settings.py`
```python
# CORS Settings - Now allows all origins in development
CORS_ALLOW_ALL_ORIGINS = True  # For development only
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ['accept', 'authorization', 'content-type', 'host', ...]
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

# ALLOWED_HOSTS - Wildcard for development
if DEBUG:
    ALLOWED_HOSTS = ['*']  # Allows all hosts
```

---

## Restart Django Server

**Important:** You MUST restart the Django server for changes to take effect.

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd F:\work\neuroceans\hrm_saas
python manage.py runserver 0.0.0.0:8000
```

**Note:** Using `0.0.0.0:8000` allows connections from any IP on your network.

---

## Test CORS Configuration

### 1. Test from Backend (should work)
```bash
curl -X POST http://192.168.10.5:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "Host: acme.localhost" \
  -d '{"email":"admin@acme.com","password":"Admin123!"}'
```

### 2. Test from Frontend Browser Console
```javascript
// Open browser on http://192.168.10.5:8080
// Run in console:
fetch('http://192.168.10.5:8000/api/v1/auth/login/', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'Host': 'acme.localhost'
  },
  body: JSON.stringify({
    email: 'admin@acme.com',
    password: 'Admin123!'
  })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

---

## Frontend Configuration

### Update API Base URL
```typescript
// .env or .env.development
VITE_API_BASE_URL=http://192.168.10.5:8000
```

### Axios Configuration
```typescript
// src/lib/api-client.ts
export const apiClient = axios.create({
  baseURL: 'http://192.168.10.5:8000',  // Use network IP
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add tenant host header
apiClient.interceptors.request.use((config) => {
  config.headers['Host'] = 'acme.localhost';  // For tenant resolution
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## Network Access Summary

| Component | Address |
|-----------|---------|
| Backend API | `http://192.168.10.5:8000` |
| Frontend | `http://192.168.10.5:8080` |
| Tenant Host Header | `acme.localhost` |

---

## Still Getting CORS Errors?

### Quick Fixes:

1. **Clear browser cache** - Try Incognito/Private mode
2. **Restart both servers** - Backend and frontend
3. **Check browser console** for exact error message
4. **Verify backend is accessible**:
   ```bash
   curl http://192.168.10.5:8000/api/v1/auth/login/
   ```

### Enable CORS Debug Logging:
```python
# config/settings.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('django.request')
logger.setLevel(logging.DEBUG)
```

---

## Production Deployment

For production, **don't use** `CORS_ALLOW_ALL_ORIGINS = True`. Instead:

```python
# config/settings.py (production)
DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://acme.yourdomain.com',
    'https://app.yourdomain.com',
]
CORS_ALLOW_CREDENTIALS = True
```

And use Nginx to serve both frontend and backend from the same domain (no CORS issues).
