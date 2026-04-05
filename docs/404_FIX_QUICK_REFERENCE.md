# Quick Fix: 404 Error on Login Endpoint

## Problem: 404 Not Found on `/api/v1/auth/login/`

**Root Cause:** The `Host` header is missing, so the multi-tenant middleware can't resolve which tenant schema to use.

---

## Solution: Add Host Header

### In Postman:

#### Option 1: Add Header Manually

1. Open your login request in Postman
2. Go to **Headers** tab
3. Add new header:

| Key | Value |
|-----|-------|
| `Host` | `acme.localhost` |

#### Option 2: Use Environment Variable

1. Make sure your Postman environment has:
   ```
   tenant_host = acme.localhost
   ```

2. In the Headers tab, add:
   ```
   Host: {{tenant_host}}
   ```

---

## Complete Request Configuration

### URL
```
POST http://127.0.0.1:8000/api/v1/auth/login/
```

### Headers
```
Content-Type: application/json
Host: acme.localhost
```

### Body (raw JSON)
```json
{
  "email": "admin@acme.com",
  "password": "Admin123!"
}
```

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Superuser | `superadmin@hrmsaas.com` | `SuperAdmin123!` |
| Admin | `admin@acme.com` | `Admin123!` |
| HR | `hr@acme.com` | `HrUser123!` |
| Employee | `employee@acme.com` | `Employee123!` |

---

## Why Host Header is Required

```
┌─────────────────────────────────────────────────────────────┐
│  Request arrives at Django                                 │
│  URL: POST /api/v1/auth/login/                            │
│  Host: acme.localhost  ← CRITICAL!                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  TenantMainMiddleware                                      │
│  1. Read Host header: "acme.localhost"                     │
│  2. Look up domains table: acme.localhost → Organization   │
│  3. Switch database schema to: "acme"                      │
│  4. Route request to correct view                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  LoginView (in acme schema)                                │
│  1. Query users table in acme schema                       │
│  2. Authenticate user                                      │
│  3. Return JWT + user data                                 │
└─────────────────────────────────────────────────────────────┘
```

**Without Host header:**
- Middleware can't determine tenant
- May use wrong schema or default behavior
- Results in 404 or authentication errors

---

## Alternative: Test with curl

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "Host: acme.localhost" \
  -d '{"email":"admin@acme.com","password":"Admin123!"}'
```

---

## Frontend Example (axios)

```typescript
const response = await axios.post(
  'http://127.0.0.1:8000/api/v1/auth/login/',
  {
    email: 'admin@acme.com',
    password: 'Admin123!'
  },
  {
    headers: {
      'Content-Type': 'application/json',
      'Host': 'acme.localhost'  // Required for tenant resolution
    }
  }
);
```

---

## Still Getting 404?

### Check 1: Verify Domain Exists in Database

```bash
python manage.py shell
>>> from tenants.models import Domain
>>> Domain.objects.all()
<QuerySet [<Domain: acme.localhost>]>
```

### Check 2: Verify Organization Schema Exists

```bash
python manage.py shell
>>> from tenants.models import Organization
>>> Organization.objects.all()
<QuerySet [<Organization: Acme Corporation>]>
```

### Check 3: Restart Django Server

Sometimes settings changes require a restart:

```bash
# Stop server (Ctrl+C)
python manage.py runserver 0.0.0.0:8000
```

---

## Summary

✅ **Always include `Host` header** for tenant resolution
✅ **Host value** = your tenant's domain (e.g., `acme.localhost`)
✅ **All API requests** need this header, not just login
