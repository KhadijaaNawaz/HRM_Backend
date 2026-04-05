# HRM SaaS Platform - Complete API Documentation

**Version:** 1.0.0
**Last Updated:** 2025-01-31
**Base URL:** `http://localhost:8000` (Development)
**API Version:** v1

---

## Table of Contents

1. [Authentication & Tenant Identification](#authentication--tenant-identification)
2. [Platform Admin Endpoints](#0-platform-admin-endpoints)
3. [Authentication Endpoints](#1-authentication-endpoints)
4. [User Management Endpoints](#2-user-management-endpoints)
5. [Role Management Endpoints](#3-role-management-endpoints)
6. [Invitation Endpoints](#4-invitation-endpoints)
7. [Organization Endpoints](#5-organization-endpoints)
8. [Attendance Endpoints](#6-attendance-endpoints)
9. [Audit Log Endpoints](#7-audit-log-endpoints)
10. [Common Error Responses](#common-error-responses)
11. [Data Models & Enums](#data-models--enums)

---

## Authentication & Tenant Identification

### Tenant Identification Methods

All tenant-specific endpoints require tenant identification. Use **ONE** of the following methods:

#### Method 1: X-Host Header (Recommended for Frontend)
```
X-Host: {tenant-subdomain}.localhost
```
Example: `X-Host: acme.localhost`

#### Method 2: x-tenant-id Header
```
x-tenant-id: {tenant-slug}
```
Example: `x-tenant-id: acme`

#### Method 3: Query Parameter
```
?tenant={tenant-slug}
```
Example: `/api/v1/auth/login/?tenant=acme`

> **NOTE:** X-Host header is recommended for frontend applications to avoid CORS issues.

### Authentication Headers

For authenticated requests:
```
Authorization: Bearer {access_token}
```

### JWT Token Management

| Token Type | Purpose | Lifetime | Usage |
|------------|---------|----------|-------|
| Access Token | API authentication | 1 hour | Include in `Authorization: Bearer` header |
| Refresh Token | Get new access token | 7 days | Send to `/api/v1/auth/token/refresh/` |

**Token Refresh Flow:**
1. Access token expires (401 Unauthorized response)
2. Call `/api/v1/auth/token/refresh/` with refresh token
3. Store new access and refresh tokens
4. Retry original request with new access token

---

## 0. Platform Admin Endpoints

**Base Path:** `/api/v1/admin/`
**Authentication:** Platform Superuser only (`is_superuser=True`)
**Tenant Identification:** NOT REQUIRED (use base URL)

### 0.1 Create New Tenant

**Endpoint:** Create New Tenant Organization

**Method + URL:**
```
POST /api/v1/admin/create-tenant/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**Request Body:**
```json
{
  "organization_name": "string (required, max 100 chars)",
  "subdomain": "string (required, slug format, unique, max 100 chars)",
  "email": "string (required, email format)",
  "password": "string (required, min 8 chars, must meet password requirements)",
  "first_name": "string (required, max 150 chars)",
  "last_name": "string (required, max 150 chars)",
  "phone": "string (optional, max 20 chars)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| organization_name | string | Yes | Name of the organization |
| subdomain | string | Yes | Unique subdomain for the tenant (e.g., "acme") |
| email | string | Yes | Email for the tenant admin user |
| password | string | Yes | Password for the tenant admin user |
| first_name | string | Yes | First name of the tenant admin |
| last_name | string | Yes | Last name of the tenant admin |
| phone | string | No | Phone number of the tenant admin |

**Success Response (201 Created):**
```json
{
  "organization": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "pending",
    "schema_name": "acme",
    "timezone": "UTC",
    "workdays": ["mon", "tue", "wed", "thu", "fri"],
    "monthly_required_days": 22,
    "public_signup_enabled": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "uuid",
    "email": "admin@acme.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "is_active": true,
    "is_tenant_admin": true,
    "is_superuser": false
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"subdomain": ["This field is required."]}` |
| 400 | `{"email": ["Enter a valid email address."]}` |
| 400 | `{"password": ["This password is too common."]}` |
| 400 | `{"error": "Organization with this subdomain already exists."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |

**Special Notes:**
- Bypasses all public signup restrictions
- Creates organization schema in database
- Creates tenant admin user with Admin role
- Returns JWT tokens for immediate login
- Subdomain must be unique across all tenants

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/create-tenant/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -d '{
    "organization_name": "Acme Corporation",
    "subdomain": "acme",
    "email": "admin@acme.com",
    "password": "TenantAdmin123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
  }'
```

**Rate Limiting:** None

---

### 0.2 List All Tenants

**Endpoint:** List All Tenants

**Method + URL:**
```
GET /api/v1/admin/tenants/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number for pagination |
| page_size | integer | No | 20 | Number of items per page |
| status | string | No | all | Filter by status: `active`, `suspended`, `pending` |
| search | string | No | - | Search by name or subdomain |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/admin/tenants/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Acme Corporation",
      "slug": "acme",
      "status": "active",
      "schema_name": "acme",
      "timezone": "UTC",
      "workdays": ["mon", "tue", "wed", "thu", "fri"],
      "monthly_required_days": 22,
      "public_signup_enabled": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "user_count": 15,
      "domain": "acme.localhost"
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |

**Special Notes:**
- Returns paginated results
- Includes user count for each tenant
- Platform superusers only

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/tenants/?page=1&page_size=20&status=active" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN"
```

**Rate Limiting:** None

---

### 0.3 Get Tenant Details

**Endpoint:** Get Tenant Details

**Method + URL:**
```
GET /api/v1/admin/tenants/{id}/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Tenant organization ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Acme Corporation",
  "slug": "acme",
  "status": "active",
  "schema_name": "acme",
  "timezone": "UTC",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "user_count": 15,
  "domain": "acme.localhost",
  "users": [
    {
      "id": "uuid",
      "email": "admin@acme.com",
      "first_name": "Admin",
      "last_name": "User",
      "is_active": true,
      "is_tenant_admin": true
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |
| 404 | `{"error": "Tenant not found."}` |

**Special Notes:**
- Includes list of tenant users
- Returns user count

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/admin/tenants/TENANT_ID/ \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN"
```

**Rate Limiting:** None

---

### 0.4 Update Tenant

**Endpoint:** Update Tenant

**Method + URL:**
```
PUT /api/v1/admin/tenants/{id}/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Tenant organization ID |

**Request Body:**
```json
{
  "name": "string (required, max 100 chars)",
  "slug": "string (required, slug format, unique, max 100 chars)",
  "timezone": "string (optional, max 50 chars)",
  "workdays": "array (optional, array of strings)",
  "monthly_required_days": "integer (optional, minimum 1)",
  "public_signup_enabled": "boolean (optional)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Organization name |
| slug | string | Yes | Unique subdomain/slug |
| timezone | string | No | Timezone (e.g., "America/New_York") |
| workdays | array | No | Working days ["mon", "tue", "wed", "thu", "fri"] |
| monthly_required_days | integer | No | Required working days per month |
| public_signup_enabled | boolean | No | Enable public signup for this tenant |

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Updated Organization Name",
  "slug": "updated-slug",
  "status": "active",
  "schema_name": "updated_slug",
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"name": ["This field is required."]}` |
| 400 | `{"slug": ["This field must be unique."]}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |
| 404 | `{"error": "Tenant not found."}` |

**Special Notes:**
- All fields required for PUT (use PATCH for partial updates)
- Changing slug requires database schema rename
- Public signup affects `/api/v1/auth/signup/` endpoint

**cURL Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/admin/tenants/TENANT_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -d '{
    "name": "Updated Organization Name",
    "slug": "updated-slug",
    "timezone": "America/New_York",
    "workdays": ["mon", "tue", "wed", "thu", "fri"],
    "monthly_required_days": 22,
    "public_signup_enabled": false
  }'
```

**Rate Limiting:** None

---

### 0.5 Partially Update Tenant

**Endpoint:** Partially Update Tenant

**Method + URL:**
```
PATCH /api/v1/admin/tenants/{id}/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Tenant organization ID |

**Request Body:**
```json
{
  "name": "string (optional)",
  "timezone": "string (optional)",
  "status": "string (optional)",
  "monthly_required_days": "integer (optional)"
}
```

All fields are optional. Only include fields you want to update.

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Acme Corporation",
  "slug": "acme",
  "status": "active",
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

**Error Responses:** Same as Update Tenant

**Special Notes:**
- Use PATCH for partial updates (only send fields to change)
- Cannot change slug via PATCH (use PUT)

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/v1/admin/tenants/TENANT_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN" \
  -d '{
    "timezone": "America/New_York",
    "monthly_required_days": 22
  }'
```

**Rate Limiting:** None

---

### 0.6 Delete Tenant

**Endpoint:** Delete Tenant

**Method + URL:**
```
DELETE /api/v1/admin/tenants/{id}/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Tenant organization ID |

**Request Body:** None

**Success Response (204 No Content):**
Empty response body

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |
| 404 | `{"error": "Tenant not found."}` |

**Special Notes:**
- **DESTRUCTIVE OPERATION** - Permanently deletes tenant and ALL data
- Deletes database schema
- Cannot be undone
- Consider using suspend instead

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/tenants/TENANT_ID/ \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN"
```

**Rate Limiting:** None

---

### 0.7 Activate Tenant

**Endpoint:** Activate Suspended Tenant

**Method + URL:**
```
POST /api/v1/admin/tenants/{id}/activate/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Tenant organization ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "message": "Tenant activated successfully.",
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active"
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "Tenant is already active."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |
| 404 | `{"error": "Tenant not found."}` |

**Special Notes:**
- Only works on suspended tenants
- Allows tenant users to login again

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/tenants/TENANT_ID/activate/ \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN"
```

**Rate Limiting:** None

---

### 0.8 Suspend Tenant

**Endpoint:** Suspend Active Tenant

**Method + URL:**
```
POST /api/v1/admin/tenants/{id}/suspend/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Tenant organization ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "message": "Tenant suspended successfully.",
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "suspended"
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "Tenant is already suspended."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |
| 404 | `{"error": "Tenant not found."}` |

**Special Notes:**
- Suspended tenants cannot login
- All API requests return 403 for suspended tenants
- Use activate to re-enable

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/tenants/TENANT_ID/suspend/ \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN"
```

**Rate Limiting:** None

---

### 0.9 List Tenant Users

**Endpoint:** List All Users for a Tenant

**Method + URL:**
```
GET /api/v1/admin/tenants/{id}/users/
```

**Authentication Required:** Yes (Platform Superuser)

**Tenant Identification:** None (platform endpoint)

**Request Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Tenant organization ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 15,
  "results": [
    {
      "id": "uuid",
      "email": "admin@acme.com",
      "first_name": "Admin",
      "last_name": "User",
      "phone": "+1234567890",
      "is_active": true,
      "is_tenant_admin": true,
      "roles": [
        {
          "id": "uuid",
          "name": "Admin",
          "description": "Tenant administrator with full access"
        }
      ],
      "date_joined": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-31T09:00:00Z"
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to perform this action."}` |
| 404 | `{"error": "Tenant not found."}` |

**Special Notes:**
- Returns all users for the specified tenant
- Includes user roles and last login

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/admin/tenants/TENANT_ID/users/ \
  -H "Authorization: Bearer YOUR_ADMIN_ACCESS_TOKEN"
```

**Rate Limiting:** None

---

## 1. Authentication Endpoints

**Base Path:** `/api/v1/auth/`
**Authentication:** Mixed (see each endpoint)

### 1.1 Login

**Endpoint:** User Login

**Method + URL:**
```
POST /api/v1/auth/login/
```

**Authentication Required:** No

**Tenant Identification:** Required (X-Host, x-tenant-id, or ?tenant=)

**Request Headers:**
```
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```
OR
```
x-tenant-id: {tenant-slug}
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tenant | string | No* | Tenant slug (if not using headers) |

*Required if not using X-Host or x-tenant-id headers

**Request Body:**
```json
{
  "email": "string (required, email format)",
  "password": "string (required)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | User password |

**Success Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "string",
    "last_name": "string",
    "phone": "string",
    "is_active": true,
    "is_tenant_admin": false,
    "is_superuser": false,
    "roles": [
      {
        "id": "uuid",
        "name": "Employee",
        "description": "Regular employee with self-service access",
        "is_system_role": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ],
    "organization": {
      "id": "uuid",
      "name": "Acme Corporation",
      "slug": "acme",
      "status": "active"
    }
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"non_field_errors": ["Unable to log in with provided credentials."]}` |
| 400 | `{"email": ["This field is required."]}` |
| 401 | `{"error": "Tenant not specified"}` |
| 403 | `{"error": "Tenant account is suspended."}` |
| 403 | `{"error": "This user account has been disabled."}` |

**Special Notes:**
- Returns JWT access token (1 hour expiry)
- Returns JWT refresh token (7 days expiry)
- Updates user's last_login timestamp
- Logs login attempt to audit logs
- Suspended tenants cannot login

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Host: acme.localhost" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!"
  }'
```

**Rate Limiting:** None

---

### 1.2 Logout

**Endpoint:** User Logout

**Method + URL:**
```
POST /api/v1/auth/logout/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "refresh": "string (required)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh | string | Yes | JWT refresh token to blacklist |

**Success Response (200 OK):**
```json
{
  "message": "Successfully logged out."
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 401 | `{"detail": "Given token not valid for any token type"}` |
| 401 | `{"error": "Tenant not specified"}` |

**Special Notes:**
- Blacklists the refresh token (if token blacklist is enabled)
- Access token will expire naturally
- Logs logout to audit logs
- Include refresh token in request body for proper logout

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

**Rate Limiting:** None

---

### 1.3 Refresh Token

**Endpoint:** Refresh Access Token

**Method + URL:**
```
POST /api/v1/auth/token/refresh/
```

**Authentication Required:** No (but requires valid refresh token)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tenant | string | No* | Tenant slug (if not using headers) |

*Required if not using X-Host header

**Request Body:**
```json
{
  "refresh": "string (required)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh | string | Yes | Valid JWT refresh token |

**Success Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Note:** The response may include a new refresh token. Always store and use the latest tokens.

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"refresh": ["This field is required."]}` |
| 401 | `{"detail": "Token is invalid or expired"}` |
| 401 | `{"detail": "Token is blacklisted"}` |
| 401 | `{"error": "Tenant not specified"}` |

**Special Notes:**
- Use this when access token expires (401 responses)
- May return a new refresh token (always use the latest)
- Refresh tokens expire after 7 days
- Implement automatic refresh in frontend interceptors

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -H "X-Host: acme.localhost" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

**Rate Limiting:** None

---

### 1.4 Get Current User

**Endpoint:** Get Current User Profile

**Method + URL:**
```
GET /api/v1/auth/me/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": false,
  "is_superuser": false,
  "roles": [
    {
      "id": "uuid",
      "name": "Employee",
      "description": "Regular employee with self-service access",
      "is_system_role": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "organization": {
    "id": "uuid",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active"
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 401 | `{"detail": "Given token not valid for any token type"}` |
| 401 | `{"error": "Tenant not specified"}` |

**Special Notes:**
- Returns profile of authenticated user
- Includes user roles and permissions
- Use to verify authentication state on app load
- Cache this data for UI permission checks

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 1.5 Forgot Password

**Endpoint:** Request Password Reset

**Method + URL:**
```
POST /api/v1/auth/password/forgot/
```

**Authentication Required:** No

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "email": "string (required, email format)",
  "redirect_url": "string (required, URL format)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| redirect_url | string | Yes | Frontend URL for password reset page |

**Success Response (200 OK):**
```json
{
  "message": "If email exists, password reset link has been sent."
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"email": ["This field is required."]}` |
| 400 | `{"email": ["Enter a valid email address."]}` |
| 429 | `{"detail": "Rate limit exceeded. Try again later."}` |

**Special Notes:**
- **Always returns success** (prevents email enumeration)
- Sends email with reset token and uid
- Token expires in 24 hours
- Redirect URL will receive ?uid=xxx&token=yyy
- **Rate limited to 5 requests per hour per IP**

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/password/forgot/ \
  -H "Content-Type: application/json" \
  -H "X-Host: acme.localhost" \
  -d '{
    "email": "user@example.com",
    "redirect_url": "http://localhost:3000/reset-password"
  }'
```

**Rate Limiting:** 5 requests per hour per IP

---

### 1.6 Reset Password

**Endpoint:** Reset Password with Token

**Method + URL:**
```
POST /api/v1/auth/password/reset/
```

**Authentication Required:** No

**Tenant Identification:** Not required (token contains tenant info)

**Request Headers:**
```
Content-Type: application/json
```

**Query Parameters:** None

**Request Body:**
```json
{
  "uid": "string (required, base64 encoded)",
  "token": "string (required)",
  "new_password": "string (required, min 8 chars)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| uid | string | Yes | Base64 encoded user ID from email |
| token | string | Yes | Password reset token from email |
| new_password | string | Yes | New password (must meet requirements) |

**Success Response (200 OK):**
```json
{
  "message": "Password reset successful."
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "Invalid or expired token."}` |
| 400 | `{"error": "Invalid reset link."}` |
| 400 | `{"new_password": ["This password is too common."]}` |
| 400 | `{"new_password": ["Password must be at least 8 characters."]}` |

**Special Notes:**
- Token expires after 24 hours
- Token is single-use only
- All user tokens are blacklisted after successful reset
- User must login again after password reset

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/password/reset/ \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "Mg",
    "token": "bk50n8-...",
    "new_password": "NewSecurePassword123!"
  }'
```

**Rate Limiting:** None

---

### 1.7 Change Password

**Endpoint:** Change Password (Authenticated)

**Method + URL:**
```
POST /api/v1/auth/password/change/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "old_password": "string (required)",
  "new_password": "string (required, min 8 chars)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| old_password | string | Yes | Current password |
| new_password | string | Yes | New password (must meet requirements) |

**Success Response (200 OK):**
```json
{
  "message": "Password changed successfully."
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"old_password": ["Old password is incorrect."]}` |
| 400 | `{"new_password": ["This password is too common."]}` |
| 400 | `{"new_password": ["Password must be at least 8 characters."]}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- Requires current password for security
- **All tokens are blacklisted** after successful change
- User must login again with new password
- Logs password change to audit logs
- Prompt user to login again after change

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/password/change/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "old_password": "OldPassword123!",
    "new_password": "NewSecurePassword456!"
  }'
```

**Rate Limiting:** None

---

## 2. User Management Endpoints

**Base Path:** `/api/v1/users/`
**Authentication:** Required (varies by role)

### 2.1 List Users

**Endpoint:** List Users

**Method + URL:**
```
GET /api/v1/users/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number |
| page_size | integer | No | 20 | Items per page |
| search | string | No | - | Search by name, email |
| role | string | No | - | Filter by role name |
| is_active | boolean | No | - | Filter by active status |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 50,
  "next": "http://acme.localhost:8000/api/v1/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "phone": "+1234567890",
      "is_active": true,
      "is_tenant_admin": false,
      "profile_picture": "http://example.com/image.jpg",
      "date_joined": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-31T09:00:00Z",
      "roles": [
        {
          "id": "uuid",
          "name": "Employee",
          "description": "Regular employee with self-service access",
          "is_system_role": true
        }
      ]
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to view users."}` |

**Special Notes:**
- **Admin/HR:** See all users
- **Employee:** See only themselves
- Returns paginated results
- Includes user roles and last login

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 2.2 Create User

**Endpoint:** Create New User

**Method + URL:**
```
POST /api/v1/users/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "email": "string (required, email format, unique)",
  "password": "string (required, min 8 chars)",
  "first_name": "string (required, max 150 chars)",
  "last_name": "string (required, max 150 chars)",
  "phone": "string (optional, max 20 chars)",
  "role_names": ["array of strings (optional)"]
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email (must be unique in tenant) |
| password | string | Yes | User password |
| first_name | string | Yes | First name |
| last_name | string | Yes | Last name |
| phone | string | No | Phone number |
| role_names | array | No | Array of role names (e.g., ["Employee", "HR"]) |

**Success Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+0987654321",
  "is_active": true,
  "is_tenant_admin": false,
  "profile_picture": null,
  "date_joined": "2024-01-31T10:00:00Z",
  "last_login": null,
  "roles": [
    {
      "id": "uuid",
      "name": "Employee",
      "description": "Regular employee with self-service access",
      "is_system_role": true
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"email": ["This field is required."]}` |
| 400 | `{"email": ["user with this email already exists."]}` |
| 400 | `{"password": ["This password is too common."]}` |
| 400 | `{"role_names": ["Role 'InvalidRole' does not exist."]}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to create users."}` |

**Special Notes:**
- **HR/Admin only** - Employees cannot create users
- Email must be unique within tenant
- Created user is active by default
- Roles are assigned if role_names provided
- Logs user creation to audit logs
- Consider using invitations instead for external users

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+0987654321",
    "role_names": ["Employee"]
  }'
```

**Rate Limiting:** None

---

### 2.3 Get User Details

**Endpoint:** Get User Details

**Method + URL:**
```
GET /api/v1/users/{id}/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | User ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": false,
  "profile_picture": "http://example.com/image.jpg",
  "date_joined": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-31T09:00:00Z",
  "roles": [
    {
      "id": "uuid",
      "name": "Employee",
      "description": "Regular employee with self-service access",
      "is_system_role": true
    }
  ],
  "user_roles": [
    {
      "id": "uuid",
      "role": {
        "id": "uuid",
        "name": "Employee",
        "description": "Regular employee with self-service access",
        "is_system_role": true
      },
      "assigned_at": "2024-01-01T00:00:00Z",
      "assigned_by_email": "admin@acme.com"
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to view this user."}` |
| 404 | `{"error": "User not found."}` |

**Special Notes:**
- **Admin/HR:** Can view any user
- **Employee:** Can only view themselves
- Includes role assignment details

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/users/USER_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 2.4 Update User

**Endpoint:** Update User (Full)

**Method + URL:**
```
PUT /api/v1/users/{id}/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | User ID |

**Request Body:**
```json
{
  "first_name": "string (required, max 150 chars)",
  "last_name": "string (required, max 150 chars)",
  "phone": "string (optional, max 20 chars)",
  "profile_picture": "string (optional, URL)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| first_name | string | Yes | First name |
| last_name | string | Yes | Last name |
| phone | string | No | Phone number |
| profile_picture | string | No | URL to profile picture |

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+1111111111",
  "is_active": true,
  "profile_picture": "http://example.com/new-image.jpg",
  "roles": [...]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"first_name": ["This field is required."]}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to update users."}` |
| 404 | `{"error": "User not found."}` |

**Special Notes:**
- **HR/Admin only**
- All fields required for PUT (use PATCH for partial)
- Cannot update email or password via this endpoint
- Logs user update to audit logs

**cURL Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/users/USER_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+1111111111",
    "profile_picture": "http://example.com/image.jpg"
  }'
```

**Rate Limiting:** None

---

### 2.5 Partially Update User

**Endpoint:** Partially Update User

**Method + URL:**
```
PATCH /api/v1/users/{id}/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | User ID |

**Request Body:**
```json
{
  "first_name": "string (optional)",
  "phone": "string (optional)",
  "profile_picture": "string (optional)"
}
```

All fields optional. Only include fields to update.

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jane Updated",
  "phone": "+1111111111",
  "is_active": true,
  "roles": [...]
}
```

**Error Responses:** Same as Update User

**Special Notes:**
- Use PATCH for partial updates
- Only send fields you want to change
- **HR/Admin only**

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/v1/users/USER_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "first_name": "Jane Updated",
    "phone": "+1111111111"
  }'
```

**Rate Limiting:** None

---

### 2.6 Delete User

**Endpoint:** Delete User (Soft Delete)

**Method + URL:**
```
DELETE /api/v1/users/{id}/
```

**Authentication Required:** Yes (Admin only)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | User ID |

**Request Body:** None

**Success Response (204 No Content):**
Empty response body

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to delete users."}` |
| 404 | `{"error": "User not found."}` |

**Special Notes:**
- **Admin only** - HR cannot delete users
- **Soft delete** - User is deactivated, not removed from database
- User `is_active` set to false
- User cannot login after deletion
- Logs user deletion to audit logs

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/users/USER_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 2.7 Get/Update Current User Profile

**Endpoint:** Current User Profile

**Method + URL:**
```
GET /api/v1/users/me/
PATCH /api/v1/users/me/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
Content-Type: application/json (for PATCH)
```

**Query Parameters:** None

**Request Body (PATCH only):**
```json
{
  "first_name": "string (optional)",
  "last_name": "string (optional)",
  "phone": "string (optional)",
  "profile_picture": "string (optional)"
}
```

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": false,
  "profile_picture": "http://example.com/image.jpg",
  "roles": [
    {
      "id": "uuid",
      "name": "Employee",
      "description": "Regular employee with self-service access",
      "is_system_role": true
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- Allows users to view/update their own profile
- Users cannot update their email via this endpoint
- Cannot change roles via this endpoint

**cURL Example:**
```bash
# Get profile
curl -X GET http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"

# Update profile
curl -X PATCH http://localhost:8000/api/v1/users/me/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "first_name": "John Updated",
    "phone": "+9999999999"
  }'
```

**Rate Limiting:** None

---

## 3. Role Management Endpoints

**Base Path:** `/api/v1/roles/`
**Authentication:** Required

### 3.1 List Roles

**Endpoint:** List All Roles

**Method + URL:**
```
GET /api/v1/roles/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "name": "Admin",
      "description": "Tenant administrator with full access within the tenant organization",
      "is_system_role": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "name": "HR",
      "description": "HR manager with user and attendance management",
      "is_system_role": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "name": "Employee",
      "description": "Regular employee with self-service access",
      "is_system_role": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- All authenticated users can view roles
- System roles (Admin, HR, Employee) are pre-created
- Custom roles can be created by admins

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/roles/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 3.2 Create Custom Role

**Endpoint:** Create Custom Role

**Method + URL:**
```
POST /api/v1/roles/
```

**Authentication Required:** Yes (Admin only)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "name": "string (required, max 100 chars, unique)",
  "description": "string (optional)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Role name (must not be system role) |
| description | string | No | Role description |

**Success Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Manager",
  "description": "Department manager with limited admin access",
  "is_system_role": false,
  "created_at": "2024-01-31T10:00:00Z",
  "updated_at": "2024-01-31T10:00:00Z"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"name": ["This field is required."]}` |
| 400 | `{"name": ["Cannot create system role \\"Admin\\"."]}` |
| 400 | `{"name": ["Role with this name already exists."]}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to create roles."}` |

**Special Notes:**
- **Admin only**
- Cannot create system roles (Admin, HR, Employee)
- System roles: `["Admin", "HR", "HR Manager", "Employee"]`

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/roles/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "name": "Manager",
    "description": "Department manager with limited admin access"
  }'
```

**Rate Limiting:** None

---

### 3.3 Get Role Details

**Endpoint:** Get Role Details

**Method + URL:**
```
GET /api/v1/roles/{id}/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Role ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Admin",
  "description": "Tenant administrator with full access within the tenant organization",
  "is_system_role": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 404 | `{"error": "Role not found."}` |

**Special Notes:**
- All authenticated users can view role details

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/roles/ROLE_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 3.4 Update Role

**Endpoint:** Update Role

**Method + URL:**
```
PATCH /api/v1/roles/{id}/
```

**Authentication Required:** Yes (Admin only)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Role ID |

**Request Body:**
```json
{
  "description": "string (optional)"
}
```

Only description can be updated.

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Manager",
  "description": "Updated role description",
  "is_system_role": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-31T10:00:00Z"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to update roles."}` |
| 404 | `{"error": "Role not found."}` |

**Special Notes:**
- **Admin only**
- Only description can be updated (not name)

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/v1/roles/ROLE_ID/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "description": "Updated role description"
  }'
```

**Rate Limiting:** None

---

### 3.5 Delete Role

**Endpoint:** Delete Role

**Method + URL:**
```
DELETE /api/v1/roles/{id}/
```

**Authentication Required:** Yes (Admin only)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Role ID |

**Request Body:** None

**Success Response (204 No Content):**
Empty response body

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "System roles cannot be deleted."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to delete roles."}` |
| 404 | `{"error": "Role not found."}` |

**Special Notes:**
- **Admin only**
- System roles cannot be deleted
- All user associations with this role are also deleted

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/roles/ROLE_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 3.6 Assign Role to User

**Endpoint:** Assign Role to User

**Method + URL:**
```
POST /api/v1/roles/{id}/assign/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Role ID |

**Request Body:**
```json
{
  "user_id": "uuid (required)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_id | string | Yes | User ID to assign role to |

**Success Response (200 OK):**
```json
{
  "message": "Role Admin assigned to user@example.com"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"user_id": ["This field is required."]}` |
| 400 | `{"error": "User already has this role."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to assign roles."}` |
| 404 | `{"error": "User not found."}` |
| 404 | `{"error": "Role not found."}` |

**Special Notes:**
- **HR/Admin only**
- A user can have multiple roles
- Logs role assignment to audit logs

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/roles/ROLE_ID/assign/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "user_id": "USER_UUID"
  }'
```

**Rate Limiting:** None

---

### 3.7 Revoke Role from User

**Endpoint:** Revoke Role from User

**Method + URL:**
```
POST /api/v1/roles/{id}/revoke/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Role ID |

**Request Body:**
```json
{
  "user_id": "uuid (required)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| user_id | string | Yes | User ID to revoke role from |

**Success Response (200 OK):**
```json
{
  "message": "Role Admin revoked from user@example.com"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"user_id": ["This field is required."]}` |
| 400 | `{"error": "User does not have this role."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to revoke roles."}` |
| 404 | `{"error": "User not found."}` |
| 404 | `{"error": "Role not found."}` |

**Special Notes:**
- **HR/Admin only**
- Logs role revocation to audit logs

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/roles/ROLE_ID/revoke/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "user_id": "USER_UUID"
  }'
```

**Rate Limiting:** None

---

## 4. Invitation Endpoints

**Base Path:** `/api/v1/invite/`
**Authentication:** Mixed (accept is public)

### 4.1 Accept Invitation

**Endpoint:** Accept Invitation

**Method + URL:**
```
POST /api/v1/invite/accept/
```

**Authentication Required:** No

**Tenant Identification:** Not required (token contains tenant info)

**Request Headers:**
```
Content-Type: application/json
```

**Query Parameters:** None

**Request Body:**
```json
{
  "token": "string (required)",
  "password": "string (required, min 8 chars)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| token | string | Yes | Invitation token from email |
| password | string | Yes | Password for new account |

**Success Response (201 Created):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "invited@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "",
    "is_active": true,
    "is_tenant_admin": false,
    "roles": [...]
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"token": ["This field is required."]}` |
| 400 | `{"error": "Invalid or expired invitation token."}` |
| 400 | `{"error": "Invitation has already been accepted."}` |
| 400 | `{"error": "Invitation has been cancelled."}` |
| 400 | `{"password": ["This password is too common."]}` |

**Special Notes:**
- **Public endpoint** - No authentication required
- Creates user account and logs in
- Returns JWT tokens for immediate login
- Token expires after 7 days
- Invitation is marked as accepted after use

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/invite/accept/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "INVITATION_TOKEN_FROM_EMAIL",
    "password": "SecurePassword123!"
  }'
```

**Rate Limiting:** None

---

### 4.2 Create Invitation

**Endpoint:** Create Invitation

**Method + URL:**
```
POST /api/v1/invite/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "email": "string (required, email format)",
  "first_name": "string (optional, max 150 chars)",
  "last_name": "string (optional, max 150 chars)",
  "role_names": ["array of strings (optional)"]
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Email to invite |
| first_name | string | No | First name (pre-fills form) |
| last_name | string | No | Last name (pre-fills form) |
| role_names | array | No | Roles to assign (defaults to Employee) |

**Success Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "token": "invitation-token-string",
  "status": "pending",
  "created_at": "2024-01-31T10:00:00Z",
  "expires_at": "2024-02-07T10:00:00Z",
  "roles": ["Employee"]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"email": ["This field is required."]}` |
| 400 | `{"email": ["User with this email already exists."]}` |
| 400 | `{"email": ["Pending invitation already sent to this email."]}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to create invitations."}` |

**Special Notes:**
- **HR/Admin only**
- Sends invitation email with accept link
- Invitation expires in 7 days
- Default role is Employee if not specified
- User account created when invitation is accepted
- Logs invitation creation to audit logs

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/invite/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role_names": ["Employee"]
  }'
```

**Rate Limiting:** None

---

### 4.3 List Invitations

**Endpoint:** List Invitations

**Method + URL:**
```
GET /api/v1/invite/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number |
| page_size | integer | No | 20 | Items per page |
| status | string | No | - | Filter by status: `pending`, `accepted`, `cancelled` |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 10,
  "results": [
    {
      "id": "uuid",
      "email": "newuser@example.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "status": "pending",
      "token": "invitation-token-string",
      "created_at": "2024-01-31T10:00:00Z",
      "expires_at": "2024-02-07T10:00:00Z",
      "accepted_at": null,
      "roles": ["Employee"],
      "invited_by": "admin@acme.com"
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to view invitations."}` |

**Special Notes:**
- **HR/Admin only**
- Returns paginated results
- Includes invitation status and expiry

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/invite/?status=pending" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 4.4 Get Invitation Details

**Endpoint:** Get Invitation Details

**Method + URL:**
```
GET /api/v1/invite/{id}/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Invitation ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "status": "pending",
  "token": "invitation-token-string",
  "created_at": "2024-01-31T10:00:00Z",
  "expires_at": "2024-02-07T10:00:00Z",
  "accepted_at": null,
  "roles": ["Employee"],
  "invited_by": "admin@acme.com"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to view invitations."}` |
| 404 | `{"error": "Invitation not found."}` |

**Special Notes:**
- **HR/Admin only**

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/invite/INVITE_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 4.5 Cancel Invitation

**Endpoint:** Cancel Invitation

**Method + URL:**
```
POST /api/v1/invite/{id}/cancel/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Invitation ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "message": "Invitation cancelled successfully.",
  "invitation": {
    "id": "uuid",
    "email": "newuser@example.com",
    "status": "cancelled"
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "Invitation has already been accepted."}` |
| 400 | `{"error": "Invitation is already cancelled."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to cancel invitations."}` |
| 404 | `{"error": "Invitation not found."}` |

**Special Notes:**
- **HR/Admin only**
- Can only cancel pending invitations
- Cancelled invitations cannot be accepted

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/invite/INVITE_ID/cancel/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 4.6 Resend Invitation

**Endpoint:** Resend Invitation

**Method + URL:**
```
POST /api/v1/invite/{id}/resend/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Invitation ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "message": "Invitation resent successfully.",
  "invitation": {
    "id": "uuid",
    "email": "newuser@example.com",
    "status": "pending",
    "expires_at": "2024-02-14T10:00:00Z"
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "Cannot resend accepted invitations."}` |
| 400 | `{"error": "Cannot resend cancelled invitations."}` |
| 400 | `{"error": "Invitation has expired."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to resend invitations."}` |
| 404 | `{"error": "Invitation not found."}` |

**Special Notes:**
- **HR/Admin only**
- Extends expiration by 7 days from resend
- Sends new email with same token

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/invite/INVITE_ID/resend/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 4.7 Resend Invitation by Email

**Endpoint:** Resend Invitation by Email

**Method + URL:**
```
POST /api/v1/invite/resend/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "email": "string (required)",
  "invite_id": "string (optional)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | No* | Email to resend invitation to |
| invite_id | string | No* | Invitation ID to resend |

*Provide either email or invite_id

**Success Response (200 OK):**
```json
{
  "message": "Invitation resent successfully."
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "Either email or invite_id must be provided."}` |
| 404 | `{"error": "No pending invitation found for this email."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to resend invitations."}` |

**Special Notes:**
- **HR/Admin only**
- Use when you have email but not invitation ID

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/invite/resend/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "email": "newuser@example.com"
  }'
```

**Rate Limiting:** None

---

## 5. Organization Endpoints

**Base Path:** `/api/v1/organization/`
**Authentication:** Required

### 5.1 Get Organization Overview

**Endpoint:** Get Organization Statistics

**Method + URL:**
```
GET /api/v1/organization/overview/
```

**Authentication Required:** Yes (HR or Admin)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "total_users": 150,
  "active_users": 145,
  "inactive_users": 5,
  "roles_count": 5,
  "attendance_today": {
    "total": 150,
    "present": 135,
    "pending": 15,
    "absent": 0
  },
  "attendance_this_month": {
    "total_days": 22,
    "avg_present_days": 20,
    "avg_hours_per_day": 8.2
  }
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to view organization overview."}` |

**Special Notes:**
- **HR/Admin only**
- Returns aggregate statistics
- Useful for dashboards

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/organization/overview/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 5.2 Get Organization Settings

**Endpoint:** Get Organization Settings

**Method + URL:**
```
GET /api/v1/organization/settings/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- All authenticated users can view settings
- Use to configure attendance rules

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/organization/settings/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 5.3 Update Organization Settings

**Endpoint:** Update Organization Settings

**Method + URL:**
```
PUT /api/v1/organization/settings/
```

**Authentication Required:** Yes (Admin only)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "timezone": "string (required, max 50 chars)",
  "workdays": ["array (required)"],
  "monthly_required_days": "integer (required, min 1)",
  "public_signup_enabled": "boolean (required)"
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timezone | string | Yes | Timezone (e.g., "America/New_York") |
| workdays | array | Yes | Working days ["mon", "tue", "wed", "thu", "fri", "sat", "sun"] |
| monthly_required_days | integer | Yes | Required working days per month |
| public_signup_enabled | boolean | Yes | Enable public signup |

**Success Response (200 OK):**
```json
{
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"timezone": ["This field is required."]}` |
| 400 | `{"monthly_required_days": ["Must be at least 1."]}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to update settings."}` |

**Special Notes:**
- **Admin only**
- Affects attendance calculations

**cURL Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/organization/settings/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "timezone": "America/New_York",
    "workdays": ["mon", "tue", "wed", "thu", "fri"],
    "monthly_required_days": 22,
    "public_signup_enabled": false
  }'
```

**Rate Limiting:** None

---

## 6. Attendance Endpoints

**Base Path:** `/api/v1/attendance/`
**Authentication:** Required

### 6.1 List Attendance Records

**Endpoint:** List Attendance Records

**Method + URL:**
```
GET /api/v1/attendance/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number |
| page_size | integer | No | 20 | Items per page |
| date | date | No | today | Filter by date (YYYY-MM-DD) |
| status | string | No | - | Filter by status |
| user | uuid | No | - | Filter by user ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 50,
  "results": [
    {
      "id": "uuid",
      "user": {
        "id": "uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "date": "2024-01-31",
      "checkin": "2024-01-31T09:00:00Z",
      "checkout": "2024-01-31T17:00:00Z",
      "status": "present",
      "hours_worked": 8.0,
      "checkin_notes": "Working from office",
      "checkout_notes": "Leaving on time",
      "checkin_location": {"lat": 40.7128, "lng": -74.0060},
      "checkout_location": {"lat": 40.7128, "lng": -74.0060}
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- **Admin/HR:** See all users
- **Employee:** See only their own records

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/attendance/?date=2024-01-31" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 6.2 Check In

**Endpoint:** Check In for the Day

**Method + URL:**
```
POST /api/v1/attendance/checkin/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "notes": "string (optional, max 500 chars)",
  "location": {
    "lat": "number (optional, decimal)",
    "lng": "number (optional, decimal)"
  }
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| notes | string | No | Check-in notes |
| location | object | No | GPS coordinates |
| location.lat | number | No | Latitude |
| location.lng | number | No | Longitude |

**Success Response (201 Created):**
```json
{
  "attendance_id": "uuid",
  "date": "2024-01-31",
  "timestamp": "2024-01-31T09:00:00Z",
  "message": "Checked in successfully"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "Already checked in today."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- Creates attendance record for today
- Cannot check in twice on same day
- Updates existing record if already checked in

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/attendance/checkin/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "notes": "Working from office",
    "location": {"lat": 40.7128, "lng": -74.0060}
  }'
```

**Rate Limiting:** None

---

### 6.3 Check Out

**Endpoint:** Check Out for the Day

**Method + URL:**
```
POST /api/v1/attendance/checkout/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**Request Body:**
```json
{
  "notes": "string (optional, max 500 chars)",
  "location": {
    "lat": "number (optional, decimal)",
    "lng": "number (optional, decimal)"
  }
}
```

**Field Descriptions:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| notes | string | No | Check-out notes |
| location | object | No | GPS coordinates |
| location.lat | number | No | Latitude |
| location.lng | number | No | Longitude |

**Success Response (200 OK):**
```json
{
  "attendance_id": "uuid",
  "date": "2024-01-31",
  "checkin": "2024-01-31T09:00:00Z",
  "checkout": "2024-01-31T17:00:00Z",
  "hours_worked": 8.0,
  "message": "Checked out successfully"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 400 | `{"error": "No check-in found for today."}` |
| 400 | `{"error": "Already checked out today."}` |
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- Requires existing check-in for the day
- Calculates hours worked

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/attendance/checkout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost" \
  -d '{
    "notes": "Leaving on time",
    "location": {"lat": 40.7128, "lng": -74.0060}
  }'
```

**Rate Limiting:** None

---

### 6.4 Get My Attendance History

**Endpoint:** Get My Attendance History

**Method + URL:**
```
GET /api/v1/attendance/my-attendance/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_date | date | No | 30 days ago | Start date (YYYY-MM-DD) |
| end_date | date | No | today | End date (YYYY-MM-DD) |
| page | integer | No | 1 | Page number |
| page_size | integer | No | 31 | Items per page |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 22,
  "results": [
    {
      "id": "uuid",
      "date": "2024-01-31",
      "checkin": "2024-01-31T09:00:00Z",
      "checkout": "2024-01-31T17:00:00Z",
      "status": "present",
      "hours_worked": 8.0,
      "notes": "Working from office"
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- Returns current user's attendance only
- Date range limited to 1 year

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/attendance/my-attendance/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 6.5 Get My Monthly Stats

**Endpoint:** Get Monthly Attendance Statistics

**Method + URL:**
```
GET /api/v1/attendance/my-monthly-stats/
```

**Authentication Required:** Yes (JWT)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| month | integer | No | current month | Month number (1-12) |
| year | integer | No | current year | Year (4-digit) |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "month": 1,
  "year": 2024,
  "total_days": 31,
  "working_days": 22,
  "present_days": 20,
  "absent_days": 2,
  "half_days": 1,
  "late_days": 3,
  "total_hours": 160.0,
  "average_hours_per_day": 8.0,
  "attendance_percentage": 90.9
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |

**Special Notes:**
- Returns current user's statistics only
- Based on organization working days

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/attendance/my-monthly-stats/?month=1&year=2024" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

## 7. Audit Log Endpoints

**Base Path:** `/api/v1/audit/`
**Authentication:** Required (Admin only)

### 7.1 List Audit Logs

**Endpoint:** List Audit Logs

**Method + URL:**
```
GET /api/v1/audit/
```

**Authentication Required:** Yes (Admin only)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number |
| page_size | integer | No | 50 | Items per page |
| action | string | No | - | Filter by action |
| user | uuid | No | - | Filter by user ID |
| target_model | string | No | - | Filter by target model |
| search | string | No | - | Search in action, target_model, target_id |
| ordering | string | No | -timestamp | Order by field |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "count": 500,
  "results": [
    {
      "id": "uuid",
      "user": "uuid",
      "user_email": "admin@acme.com",
      "user_name": "Admin User",
      "action": "user.login",
      "target_model": "User",
      "target_id": "uuid",
      "ip_address": "192.168.1.1",
      "meta": {
        "user_agent": "Mozilla/5.0..."
      },
      "timestamp": "2024-01-31T09:00:00Z"
    }
  ]
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to view audit logs."}` |

**Special Notes:**
- **Admin only**
- Ordered by newest first (default)
- Used for compliance and security auditing

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/audit/?action=user.login&page=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

### 7.2 Get Audit Log Details

**Endpoint:** Get Audit Log Entry

**Method + URL:**
```
GET /api/v1/audit/{id}/
```

**Authentication Required:** Yes (Admin only)

**Tenant Identification:** Required

**Request Headers:**
```
Authorization: Bearer {access_token}
X-Host: {tenant-subdomain}.localhost
```

**Query Parameters:** None

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Audit log ID |

**Request Body:** None

**Success Response (200 OK):**
```json
{
  "id": "uuid",
  "user": "uuid",
  "user_email": "admin@acme.com",
  "user_name": "Admin User",
  "action": "user.created",
  "target_model": "User",
  "target_id": "uuid",
  "ip_address": "192.168.1.1",
  "meta": {
    "created_email": "newuser@example.com"
  },
  "timestamp": "2024-01-31T09:00:00Z"
}
```

**Error Responses:**

| Status | Error |
|--------|-------|
| 401 | `{"detail": "Authentication credentials were not provided."}` |
| 403 | `{"error": "You do not have permission to view audit logs."}` |
| 404 | `{"error": "Audit log not found."}` |

**Special Notes:**
- **Admin only**

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/v1/audit/AUDIT_ID/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "X-Host: acme.localhost"
```

**Rate Limiting:** None

---

## Common Error Responses

### Standard Error Format

Most errors follow this format:

```json
{
  "error": "Error message description"
}
```

Or for validation errors:

```json
{
  "field_name": ["Error message 1", "Error message 2"]
}
```

### Common HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 OK | Request successful |
| 201 Created | Resource created |
| 204 No Content | Successful deletion |
| 400 Bad Request | Invalid request data |
| 401 Unauthorized | Authentication required or invalid |
| 403 Forbidden | Insufficient permissions |
| 404 Not Found | Resource not found |
| 429 Too Many Requests | Rate limit exceeded |
| 500 Internal Server Error | Server error |

---

## Data Models & Enums

### User Status

| Value | Description |
|-------|-------------|
| true | User is active and can login |
| false | User is deactivated (soft delete) |

### Organization Status

| Value | Description |
|-------|-------------|
| active | Organization is active |
| suspended | Organization is suspended (no login) |
| pending | Organization pending activation |

### Invitation Status

| Value | Description |
|-------|-------------|
| pending | Invitation not yet accepted |
| accepted | Invitation accepted, user created |
| cancelled | Invitation cancelled |
| expired | Invitation expired (7 days) |

### Attendance Status

| Value | Description |
|-------|-------------|
| present | User checked in and out |
| absent | User did not check in |
| half_day | User worked half day |
| pending | User checked in, not checked out |

### Workdays

| Value | Description |
|-------|-------------|
| mon | Monday |
| tue | Tuesday |
| wed | Wednesday |
| thu | Thursday |
| fri | Friday |
| sat | Saturday |
| sun | Sunday |

### System Roles

| Role | Description | Can Delete |
|------|-------------|------------|
| Admin | Full tenant access | No |
| HR | User and attendance management | No |
| HR Manager | HR with additional permissions | No |
| Employee | Self-service access | No |

---

## Password Requirements

Passwords must satisfy Django's default password validators:

| Requirement | Description |
|-------------|-------------|
| Length | Minimum 8 characters |
| Common | Cannot be too common (e.g., "password") |
| Numeric | Cannot be entirely numeric |
| Similar | Cannot be similar to user's personal info |
| Complexity | Must contain letters and numbers |

---

## Quick Reference: User Roles

### Platform Superuser (`is_superuser=True`)
- All Platform Admin endpoints
- Create/manage/delete tenants
- View all tenant users

### Tenant Admin (`is_tenant_admin=True`)
- All User endpoints (CRUD)
- All Role endpoints
- All Invitation endpoints
- Organization settings (read/write)
- Attendance (view all)
- Audit logs (view)

### HR
- User endpoints (view, create, update)
- Invitation endpoints
- Attendance (view all, manage)
- Organization settings (read only)

### Employee
- Own profile (view, update)
- Attendance (check in/out, view own)
- Organization settings (read only)

---

## Testing Credentials

### Acme Tenant (Development)

```
Tenant Subdomain: acme
Email: admin@acme.com
Password: Admin123!
Role: Tenant Admin
```

### Platform Superuser (Development)

```
Email: superadmin@hrmsaas.com
Password: SuperAdmin123!
Role: Platform Superuser
```

---

## Appendix: Complete Endpoint List

### Platform Admin (`/api/v1/admin/`)
- `POST /create-tenant/` - Create new tenant
- `GET /tenants/` - List all tenants
- `POST /tenants/` - Create tenant (alternate)
- `GET /tenants/{id}/` - Get tenant details
- `PUT /tenants/{id}/` - Update tenant
- `PATCH /tenants/{id}/` - Partially update tenant
- `DELETE /tenants/{id}/` - Delete tenant
- `POST /tenants/{id}/activate/` - Activate tenant
- `POST /tenants/{id}/suspend/` - Suspend tenant
- `GET /tenants/{id}/users/` - List tenant users

### Authentication (`/api/v1/auth/`)
- `POST /login/` - Login
- `POST /logout/` - Logout
- `POST /token/refresh/` - Refresh token
- `GET /me/` - Get current user
- `POST /password/forgot/` - Forgot password
- `POST /password/reset/` - Reset password
- `POST /password/change/` - Change password

### Users (`/api/v1/users/`)
- `GET /users/` - List users
- `POST /users/` - Create user
- `GET /users/{id}/` - Get user
- `PUT /users/{id}/` - Update user
- `PATCH /users/{id}/` - Partially update user
- `DELETE /users/{id}/` - Delete user
- `GET /users/me/` - Get current user
- `PATCH /users/me/` - Update current user

### Roles (`/api/v1/roles/`)
- `GET /roles/` - List roles
- `POST /roles/` - Create role
- `GET /roles/{id}/` - Get role
- `PATCH /roles/{id}/` - Update role
- `DELETE /roles/{id}/` - Delete role
- `POST /roles/{id}/assign/` - Assign role
- `POST /roles/{id}/revoke/` - Revoke role

### Invitations (`/api/v1/invite/`)
- `POST /accept/` - Accept invitation
- `POST /resend/` - Resend by email
- `GET /invite/` - List invitations
- `POST /invite/` - Create invitation
- `GET /invite/{id}/` - Get invitation
- `PATCH /invite/{id}/` - Update invitation
- `DELETE /invite/{id}/` - Delete invitation
- `POST /invite/{id}/cancel/` - Cancel invitation
- `POST /invite/{id}/resend/` - Resend invitation

### Organization (`/api/v1/organization/`)
- `GET /overview/` - Get statistics
- `GET /settings/` - Get settings
- `PUT /settings/` - Update settings

### Attendance (`/api/v1/attendance/`)
- `GET /attendance/` - List records
- `GET /attendance/{id}/` - Get record
- `POST /attendance/checkin/` - Check in
- `POST /attendance/checkout/` - Check out
- `GET /attendance/my-attendance/` - My history
- `GET /attendance/my-monthly-stats/` - My stats

### Audit Logs (`/api/v1/audit/`)
- `GET /audit/` - List logs
- `GET /audit/{id}/` - Get log entry

---

**Document Version:** 1.0.0
**Last Updated:** 2025-01-31
**For questions or support, contact the backend team.**
