# Authentication API Reference for Frontend Developers

## Overview

This document provides detailed information about the Authentication APIs for the HRM SaaS application. These APIs are designed for frontend integration with JWT-based authentication.

## Base URL

- **Development**: `http://localhost:8000`
- **API Version**: `v1`

## Multi-Tenancy Architecture

This is a multi-tenant application where tenants are identified via subdomain or query parameter.

### Tenant Identification Methods

1. **Via X-Host Header (Recommended for Frontend)**: Send hostname from frontend
   - Example: `X-Host: acme.localhost` or `X-Host: acme.yourapp.com`
   - Extract subdomain automatically: `acme` from `acme.localhost`
   ```javascript
   headers: {
     'X-Host': window.location.hostname
   }
   ```

2. **Via x-tenant-id Header**: Direct tenant slug
   - Example: `x-tenant-id: acme`
   - Use when you have the tenant slug directly

3. **Via Query Parameter**: `/api/v1/auth/login/?tenant=tenant-slug`
   - Example: `http://localhost:8000/api/v1/auth/login/?tenant=acme`

4. **Via Host Header**: Original subdomain method
   - Example: `Host: acme.localhost:8000`
   - Note: May cause CORS issues in some browsers

> **Note**: Most authentication endpoints require tenant identification. The `X-Host` header method is recommended for frontend applications as it avoids CORS issues and works seamlessly with single-page applications.

---

## Authentication Endpoints

### 1. Login

**Endpoint**: `POST /api/v1/auth/login/`

**Description**: Authenticates a user and returns JWT tokens (access and refresh).

**Headers** (choose one method):

**Option A: Using X-Host Header (Recommended for Frontend)**
```
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```
Example: `X-Host: acme.localhost`

**Option B: Using x-tenant-id Header**
```
Content-Type: application/json
x-tenant-id: {tenant-slug}
```
Example: `x-tenant-id: acme`

**Option C: Using Host Header (may cause CORS issues)**
```
Content-Type: application/json
Host: {tenant-subdomain}.localhost:8000
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "UserPassword123!"
}
```

**Success Response** (200 OK):
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "email": "admin@acme.com",
    "first_name": "Admin",
    "last_name": "User",
    "phone": "",
    "is_active": true,
    "is_tenant_admin": true,
    "is_superuser": false,
    "roles": [
      {
        "id": "d9870c08-6df3-43ea-bc5a-2d0a77b8c93c",
        "name": "Admin",
        "description": "Tenant administrator with full access within the tenant organization",
        "is_system_role": true,
        "created_at": "2026-03-03T22:11:43.930978Z",
        "updated_at": "2026-03-03T22:11:43.930991Z"
      }
    ],
    "organization": null
  }
}
```

**Error Responses**:

- **400 Bad Request** (Invalid credentials):
```json
{
  "error": true,
  "message": "Unable to log in with provided credentials.",
  "non_field_errors": ["Unable to log in with provided credentials."]
}
```

- **403 Forbidden** (Suspended tenant):
```json
{
  "error": "Tenant account is suspended."
}
```

---

### 2. Get Current User (Me)

**Endpoint**: `GET /api/v1/auth/me/`

**Description**: Returns the current authenticated user's information.

**Headers**:
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

Example:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Host: acme.localhost
```

**Success Response** (200 OK):
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "email": "admin@acme.com",
  "first_name": "Admin",
  "last_name": "User",
  "phone": "",
  "is_active": true,
  "is_tenant_admin": true,
  "is_superuser": false,
  "roles": [
    {
      "id": "d9870c08-6df3-43ea-bc5a-2d0a77b8c93c",
      "name": "Admin",
      "description": "Tenant administrator with full access within the tenant organization",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.930978Z",
      "updated_at": "2026-03-03T22:11:43.930991Z"
    }
  ],
  "organization": {
    "id": "...",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active"
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 3. Refresh Token

**Endpoint**: `POST /api/v1/auth/token/refresh/`

**Description**: Obtains a new access token using a valid refresh token.

**Headers** (choose one):
```
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```

OR

```
Content-Type: application/json
x-tenant-id: {tenant-slug}
```

**Request Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

---

### 4. Logout

**Endpoint**: `POST /api/v1/auth/logout/`

**Description**: Logs out the user by blacklisting the refresh token.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```

**Request Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "message": "Successfully logged out."
}
```

---

### 5. Forgot Password

**Endpoint**: `POST /api/v1/auth/password/forgot/`

**Description**: Initiates password reset by sending an email with reset link.

**Headers**:
```
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "redirect_url": "http://localhost:3000/reset-password"
}
```

**Success Response** (200 OK):
```json
{
  "message": "If email exists, password reset link has been sent."
}
```

> **Note**: This endpoint always returns success to prevent email enumeration attacks.

**Rate Limiting**: 5 requests per hour per IP address.

---

### 6. Reset Password

**Endpoint**: `POST /api/v1/auth/password/reset/`

**Description**: Resets user password using the token from the password reset email.

**Headers**:
```
Content-Type: application/json
```

**Query Parameters**:
- `tenant` (optional): The tenant slug

**Request Body**:
```json
{
  "uid": "Mg",  // Base64 encoded user ID
  "token": "bk50n8-...",  // Token from email
  "new_password": "NewSecurePassword123!"
}
```

**Success Response** (200 OK):
```json
{
  "message": "Password reset successful."
}
```

**Error Responses**:

- **400 Bad Request** (Invalid/expired token):
```json
{
  "error": "Invalid or expired token."
}
```

- **400 Bad Request** (Invalid reset link):
```json
{
  "error": "Invalid reset link."
}
```

---

### 7. Change Password

**Endpoint**: `POST /api/v1/auth/password/change/`

**Description**: Changes password for an authenticated user.

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```

**Request Body**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Success Response** (200 OK):
```json
{
  "message": "Password changed successfully."
}
```

**Error Response** (400 Bad Request):
```json
{
  "old_password": ["Old password is incorrect."]
}
```

**Important**: After successful password change, all tokens are blacklisted and the user must log in again.

---

## Token Management

### Access Token

- **Lifetime**: 1 hour (configurable)
- **Usage**: Include in `Authorization: Bearer {access_token}` header
- **Storage**: Store in memory or secure storage (not localStorage for security)

### Refresh Token

- **Lifetime**: 7 days (configurable)
- **Usage**: Use to obtain new access tokens
- **Storage**: Store securely (httpOnly cookie recommended)

### Token Refresh Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. User logs in → Receive access + refresh tokens           │
│  2. Use access token for API requests                        │
│  3. When access token expires (401 error):                   │
│     → Call /api/v1/auth/token/refresh/ with refresh token    │
│     → Receive new access + refresh tokens                    │
│     → Update stored tokens                                   │
│  4. If refresh fails (401 error):                            │
│     → Redirect user to login page                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Password Requirements

Passwords must satisfy Django's default password validators:
- Minimum length: 8 characters
- Cannot be too common (e.g., "password123")
- Cannot be entirely numeric
- Cannot be similar to user's personal information
- Must contain at least one letter and one character

---

## Error Handling

### Common HTTP Status Codes

| Status | Description |
|--------|-------------|
| 200 OK | Request successful |
| 201 Created | Resource created successfully |
| 400 Bad Request | Invalid request data |
| 401 Unauthorized | Authentication required or invalid |
| 403 Forbidden | Insufficient permissions |
| 404 Not Found | Resource not found |
| 429 Too Many Requests | Rate limit exceeded |

### Error Response Format

```json
{
  "error": true,
  "message": "Error message description",
  "detail": "Detailed error information",
  "field_name": ["Specific field error"]
}
```

---

## Frontend Integration Examples

### React Example

```typescript
// api/auth.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  access: string;
  refresh: string;
  user: UserInfo;
}

interface UserInfo {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_tenant_admin: boolean;
  roles: Role[];
}

// Get current hostname for X-Host header
const getHostName = (): string => {
  return window.location.hostname;
};

// Login
export const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Host': getHostName(),
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Login failed');
  }

  return response.json();
};

// Get current user
export const getCurrentUser = async (token: string): Promise<UserInfo> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me/`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Host': getHostName(),
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }

  return response.json();
};

// Refresh token
export const refreshToken = async (refreshToken: string): Promise<{ access: string; refresh: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/token/refresh/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Host': getHostName(),
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });

  if (!response.ok) {
    throw new Error('Token refresh failed');
  }

  return response.json();
};

// Logout
export const logout = async (token: string, refreshToken: string): Promise<void> => {
  await fetch(`${API_BASE_URL}/api/v1/auth/logout/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Host': getHostName(),
    },
    body: JSON.stringify({ refresh: refreshToken }),
  });
};
```

### Axios Interceptor Example

```typescript
// utils/axiosInterceptor.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
});

// Request interceptor - Add X-Host header for tenant identification
api.interceptors.request.use((config) => {
  // Add X-Host header with current hostname
  config.headers['X-Host'] = window.location.hostname;
  return config;
});

// Response interceptor - Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const { data } = await axios.post('/api/v1/auth/token/refresh/', {
          refresh: getRefreshToken(),
        }, {
          headers: {
            'X-Host': window.location.hostname,
          },
        });

        setAccessToken(data.access);
        setRefreshToken(data.refresh);

        originalRequest.headers['Authorization'] = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        clearAuthTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

---

## Testing

### Test Credentials (Acme Tenant)

```
Email: admin@acme.com
Password: Admin123!
Tenant: acme
```

### Test with cURL

**Using X-Host Header (Recommended)**:
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Host: acme.localhost" \
  -d '{"email": "admin@acme.com", "password": "Admin123!"}'

# Get current user
curl -X GET http://localhost:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -H "X-Host: acme.localhost" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

**Using x-tenant-id Header**:
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "x-tenant-id: acme" \
  -d '{"email": "admin@acme.com", "password": "Admin123!"}'
```

**Using Query Parameter**:
```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login/?tenant=acme" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@acme.com", "password": "Admin123!"}'
```

---

## CORS Configuration

For frontend integration, ensure CORS is properly configured in your Django settings:

```python
# config/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add your production frontend URLs
]

CORS_ALLOW_CREDENTIALS = True
```

---

## Security Best Practices

1. **Always use HTTPS** in production
2. **Store tokens securely**:
   - Access tokens: Memory or secure storage
   - Refresh tokens: httpOnly cookies (recommended)
3. **Implement proper logout**: Clear tokens from storage
4. **Handle token expiry gracefully** with automatic refresh
5. **Never expose refresh tokens** in URL parameters or localStorage
6. **Validate user permissions** on the frontend based on role data
7. **Implement rate limiting** on the frontend for login attempts

---

## Support

For API issues or questions, please contact the backend team or refer to the main API documentation at `HRM_SaaS_Complete_API.postman_collection.json`.
