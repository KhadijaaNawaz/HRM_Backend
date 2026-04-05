# HRM SaaS API - Complete Postman Guide

This guide provides complete instructions for testing the HRM SaaS backend APIs using Postman.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Testing Workflow](#testing-workflow)
5. [Common Errors & Solutions](#common-errors--solutions)

---

## Environment Setup

### Step 1: Add Tenant to Hosts File

Add the test tenant to your system hosts file:

**Windows:** `C:\Windows\System32\drivers\etc\hosts`
```
127.0.0.1  acme.localhost
```

**Linux/Mac:** `/etc/hosts`
```
127.0.0.1  acme.localhost
```

### Step 2: Start the Django Server

```bash
cd /path/to/hrm_saas
python manage.py runserver 127.0.0.1:8000
```

### Step 3: Configure Postman Environment

Create a new environment in Postman with the following variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://127.0.0.1:8000` | API base URL |
| `tenant_host` | `acme.localhost` | Tenant domain for Host header |
| `access_token` | `{{access_token}}` | JWT access token (auto-set after login) |
| `refresh_token` | `{{refresh_token}}` | JWT refresh token (auto-set after login) |
| `user_id` | `{{user_id}}` | Current user ID (auto-set after login) |

---

## Authentication

### 1. Login

**Endpoint:** `POST /api/v1/auth/login/`

**Headers:**
```
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "email": "admin@acme.com",
  "password": "Admin123!"
}
```

**Test Credentials:**

| Role | Email | Password |
|------|-------|----------|
| Superuser | `superadmin@hrmsaas.com` | `SuperAdmin123!` |
| Tenant Admin | `admin@acme.com` | `Admin123!` |
| HR | `hr@acme.com` | `HrUser123!` |
| Employee | `employee@acme.com` | `Employee123!` |

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "admin@acme.com",
    "first_name": "Admin",
    "last_name": "User",
    "is_active": true,
    "is_tenant_admin": true,
    "is_superuser": false,
    "roles": [
      {
        "id": "d9870c08-6df3-43ea-bc5a-2d0a77b8c93c",
        "name": "Admin",
        "description": "Tenant administrator with full access within the tenant organization",
        "is_system_role": true
      }
    ]
  }
}
```

**Postman Test Script (auto-save tokens):**
```javascript
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set('access_token', response.access);
    pm.environment.set('refresh_token', response.refresh);
    pm.environment.set('user_id', response.user.id);
}
```

### 2. Get Current User

**Endpoint:** `GET /api/v1/auth/me/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
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
    "id": "org-id",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active"
  }
}
```

### 3. Refresh Token

**Endpoint:** `POST /api/v1/auth/token/refresh/`

**Headers:**
```
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "refresh": "{{refresh_token}}"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4. Logout

**Endpoint:** `POST /api/v1/auth/logout/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "refresh": "{{refresh_token}}"
}
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out."
}
```

### 5. Change Password

**Endpoint:** `POST /api/v1/auth/password/change/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "old_password": "Admin123!",
  "new_password": "NewPassword456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully."
}
```

### 6. Forgot Password

**Endpoint:** `POST /api/v1/auth/password/forgot/`

**Headers:**
```
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "email": "admin@acme.com",
  "redirect_url": "http://localhost:3000/reset-password"
}
```

**Response (200 OK):**
```json
{
  "message": "If email exists, password reset link has been sent."
}
```

### 7. Reset Password

**Endpoint:** `POST /api/v1/auth/password/reset/`

**Headers:**
```
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "uid": "base64_encoded_user_id",
  "token": "password_reset_token",
  "new_password": "NewPassword456!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successful."
}
```

---

## API Endpoints

### Admin Endpoints (Superuser Only)

### 1. Create Tenant Organization

**Endpoint:** `POST /api/v1/admin/create-tenant/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "name": "TechCorp Inc.",
  "slug": "techcorp",
  "domain": "techcorp.localhost",
  "admin_email": "admin@techcorp.com",
  "admin_password": "Admin123!",
  "admin_first_name": "Tech",
  "admin_last_name": "Admin"
}
```

**Response (201 Created):**
```json
{
  "id": "tenant-id",
  "name": "TechCorp Inc.",
  "slug": "techcorp",
  "schema_name": "techcorp",
  "status": "pending",
  "domain": "techcorp.localhost"
}
```

### 2. List All Tenants

**Endpoint:** `GET /api/v1/admin/tenants/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "tenant-id-1",
      "name": "Acme Corporation",
      "slug": "acme",
      "status": "active",
      "created_at": "2026-03-03T22:11:43.000000Z"
    }
  ]
}
```

---

### User Management Endpoints

### 1. List Users

**Endpoint:** `GET /api/v1/users/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Query Parameters:**
- `page` (optional): Page number
- `page_size` (optional): Items per page (default: 20)

**Response (200 OK):**
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "user-id-1",
      "email": "admin@acme.com",
      "first_name": "Admin",
      "last_name": "User",
      "phone": "",
      "is_active": true,
      "is_tenant_admin": true,
      "profile_picture": null,
      "date_joined": "2026-03-03T22:11:43.000000Z",
      "last_login": "2026-03-04T03:20:11.000000Z",
      "roles": [
        {
          "id": "role-id-1",
          "name": "Admin",
          "description": "Tenant administrator with full access within the tenant organization",
          "is_system_role": true
        }
      ]
    }
  ]
}
```

**Permission Required:** HR or Admin

### 2. Get User Details

**Endpoint:** `GET /api/v1/users/:id/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "id": "user-id-1",
  "email": "admin@acme.com",
  "first_name": "Admin",
  "last_name": "User",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": true,
  "profile_picture": "http://127.0.0.1:8000/media/profile_pics/photo.jpg",
  "date_joined": "2026-03-03T22:11:43.000000Z",
  "last_login": "2026-03-04T03:20:11.000000Z",
  "roles": [
    {
      "id": "role-id-1",
      "name": "Admin",
      "description": "Tenant administrator with full access within the tenant organization",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.930978Z",
      "updated_at": "2026-03-03T22:11:43.930991Z"
    }
  ],
  "user_roles": [
    {
      "id": "user-role-id-1",
      "role": {
        "id": "role-id-1",
        "name": "Admin",
        "description": "Tenant administrator with full access within the tenant organization",
        "is_system_role": true
      },
      "role_id": "role-id-1",
      "assigned_at": "2026-03-03T22:11:43.000000Z",
      "assigned_by_email": "superadmin@hrmsaas.com"
    }
  ]
}
```

### 3. Create User

**Endpoint:** `POST /api/v1/users/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "email": "john.doe@acme.com",
  "password": "JohnDoe123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "role_names": ["Employee"]
}
```

**Response (201 Created):**
```json
{
  "id": "new-user-id",
  "email": "john.doe@acme.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": false,
  "profile_picture": null,
  "date_joined": "2026-03-04T10:00:00.000000Z",
  "roles": [
    {
      "id": "employee-role-id",
      "name": "Employee",
      "is_system_role": true
    }
  ]
}
```

**Permission Required:** HR or Admin

### 4. Update User

**Endpoint:** `PATCH /api/v1/users/:id/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "first_name": "John Updated",
  "phone": "+9876543210"
}
```

**Response (200 OK):**
```json
{
  "id": "user-id",
  "email": "john.doe@acme.com",
  "first_name": "John Updated",
  "last_name": "Doe",
  "phone": "+9876543210",
  "is_active": true
}
```

**Permission Required:** HR or Admin (or self for own profile)

### 5. Delete User (Soft Delete)

**Endpoint:** `DELETE /api/v1/users/:id/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (204 No Content)**

**Permission Required:** HR or Admin

### 6. Update Current User Profile

**Endpoint:** `GET/PATCH /api/v1/users/me/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json (for PATCH)
Host: {{tenant_host}}
```

**PATCH Body:**
```json
{
  "first_name": "Updated First Name",
  "last_name": "Updated Last Name",
  "phone": "+1234567890"
}
```

**Response (200 OK):**
```json
{
  "id": "user-id",
  "email": "user@acme.com",
  "first_name": "Updated First Name",
  "last_name": "Updated Last Name",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": false,
  "is_superuser": false,
  "roles": [
    {
      "id": "role-id",
      "name": "Employee",
      "description": "Regular employee with access to own attendance and profile",
      "is_system_role": true
    }
  ],
  "organization": {
    "id": "org-id",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active"
  }
}
```

---

### Role Management Endpoints

### 1. List Roles

**Endpoint:** `GET /api/v1/roles/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "id": "role-id-1",
      "name": "Admin",
      "description": "Tenant administrator with full access within the tenant organization",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.930978Z",
      "updated_at": "2026-03-03T22:11:43.930991Z"
    },
    {
      "id": "role-id-2",
      "name": "HR",
      "description": "HR user with access to user management and attendance tracking",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.934053Z",
      "updated_at": "2026-03-03T22:11:43.934064Z"
    },
    {
      "id": "role-id-3",
      "name": "Employee",
      "description": "Regular employee with access to own attendance and profile",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.935654Z",
      "updated_at": "2026-03-03T22:11:43.935664Z"
    }
  ]
}
```

### 2. Get Role Details

**Endpoint:** `GET /api/v1/roles/:id/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "id": "role-id-1",
  "name": "Admin",
  "description": "Tenant administrator with full access within the tenant organization",
  "is_system_role": true,
  "created_at": "2026-03-03T22:11:43.930978Z",
  "updated_at": "2026-03-03T22:11:43.930991Z"
}
```

### 3. Create Custom Role

**Endpoint:** `POST /api/v1/roles/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "name": "Project Manager",
  "description": "Can manage projects and view team attendance"
}
```

**Response (201 Created):**
```json
{
  "id": "new-role-id",
  "name": "Project Manager",
  "description": "Can manage projects and view team attendance",
  "is_system_role": false,
  "created_at": "2026-03-04T10:00:00.000000Z",
  "updated_at": "2026-03-04T10:00:00.000000Z"
}
```

**Permission Required:** Tenant Admin

**Note:** Cannot create system roles (Admin, HR, Employee)

### 4. Update Role

**Endpoint:** `PATCH /api/v1/roles/:id/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "description": "Updated description"
}
```

**Response (200 OK):**
```json
{
  "id": "role-id",
  "name": "Project Manager",
  "description": "Updated description",
  "is_system_role": false
}
```

**Permission Required:** Tenant Admin

### 5. Delete Role

**Endpoint:** `DELETE /api/v1/roles/:id/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (204 No Content)**

**Permission Required:** Tenant Admin

**Note:** System roles cannot be deleted

### 6. Assign Role to User

**Endpoint:** `POST /api/v1/roles/:id/assign/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "user_id": "user-uuid"
}
```

**Response (200 OK):**
```json
{
  "message": "Role HR assigned to john.doe@acme.com"
}
```

**Permission Required:** Tenant Admin

### 7. Revoke Role from User

**Endpoint:** `POST /api/v1/roles/:id/revoke/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "user_id": "user-uuid"
}
```

**Response (200 OK):**
```json
{
  "message": "Role HR revoked from john.doe@acme.com"
}
```

**Permission Required:** Tenant Admin

---

### Invitation Endpoints

### 1. List Invitations

**Endpoint:** `GET /api/v1/invite/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `accepted`, `expired`, `cancelled`)
- `page` (optional): Page number

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "invite-id-1",
      "email": "new.user@example.com",
      "role": "Employee",
      "status": "pending",
      "invited_by": "admin@acme.com",
      "created_at": "2026-03-04T10:00:00.000000Z",
      "expires_at": "2026-03-11T10:00:00.000000Z"
    }
  ]
}
```

**Permission Required:** HR or Admin

### 2. Create Invitation

**Endpoint:** `POST /api/v1/invite/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "email": "new.user@example.com",
  "role": "Employee",
  "redirect_url": "http://localhost:3000/accept-invite"
}
```

**Response (201 Created):**
```json
{
  "id": "invite-id",
  "email": "new.user@example.com",
  "role": "Employee",
  "status": "pending",
  "invited_by": "admin@acme.com",
  "created_at": "2026-03-04T10:00:00.000000Z",
  "expires_at": "2026-03-11T10:00:00.000000Z",
  "token": "unique-invitation-token"
}
```

**Permission Required:** HR or Admin

### 3. Accept Invitation

**Endpoint:** `POST /api/v1/invite/accept/`

**Headers:**
```
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "token": "invitation-token",
  "password": "NewUser123!",
  "first_name": "New",
  "last_name": "User"
}
```

**Response (200 OK):**
```json
{
  "message": "Invitation accepted successfully.",
  "user": {
    "id": "new-user-id",
    "email": "new.user@example.com",
    "first_name": "New",
    "last_name": "User",
    "is_active": true
  }
}
```

### 4. Cancel Invitation

**Endpoint:** `DELETE /api/v1/invite/:id/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (204 No Content)**

**Permission Required:** HR or Admin

### 5. Resend Invitation

**Endpoint:** `POST /api/v1/invite/resend/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "email": "new.user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Invitation resent to new.user@example.com"
}
```

**Permission Required:** HR or Admin

---

### Attendance Endpoints

### 1. List Attendance Records

**Endpoint:** `GET /api/v1/attendance/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Query Parameters:**
- `user_id` (optional): Filter by user (HR/Admin only)
- `date_from` (optional): Filter by date range start (YYYY-MM-DD)
- `date_to` (optional): Filter by date range end (YYYY-MM-DD)
- `status` (optional): Filter by status (`present`, `absent`, `late`, `half_day`)
- `page` (optional): Page number

**Response (200 OK):**
```json
{
  "count": 20,
  "results": [
    {
      "id": "attendance-id-1",
      "user": {
        "id": "user-id-1",
        "email": "john.doe@acme.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "date": "2026-03-04",
      "check_in": "2026-03-04T09:00:00Z",
      "check_out": "2026-03-04T18:00:00Z",
      "status": "present",
      "work_hours": 9.0,
      "notes": ""
    }
  ]
}
```

### 2. Check In

**Endpoint:** `POST /api/v1/attendance/check-in/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body (Optional):**
```json
{
  "notes": "Working from home",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

**Response (201 Created):**
```json
{
  "id": "attendance-id",
  "user": {
    "id": "user-id",
    "email": "john.doe@acme.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "date": "2026-03-04",
  "check_in": "2026-03-04T09:00:00.000000Z",
  "check_out": null,
  "status": "present",
  "work_hours": 0,
  "notes": "Working from home",
  "check_in_location": {"latitude": 40.7128, "longitude": -74.0060}
}
```

### 3. Check Out

**Endpoint:** `POST /api/v1/attendance/check-out/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body (Optional):**
```json
{
  "notes": "Completed all tasks",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

**Response (200 OK):**
```json
{
  "id": "attendance-id",
  "user": {
    "id": "user-id",
    "email": "john.doe@acme.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "date": "2026-03-04",
  "check_in": "2026-03-04T09:00:00.000000Z",
  "check_out": "2026-03-04T18:00:00.000000Z",
  "status": "present",
  "work_hours": 9.0,
  "notes": "Completed all tasks"
}
```

### 4. Get Attendance Report

**Endpoint:** `GET /api/v1/attendance/report/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Query Parameters:**
- `user_id` (optional): Filter by user (HR/Admin only)
- `month` (optional): Month number (1-12)
- `year` (optional): Year (YYYY)

**Response (200 OK):**
```json
{
  "user": {
    "id": "user-id",
    "email": "john.doe@acme.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "period": {
    "month": 3,
    "year": 2026,
    "month_name": "March"
  },
  "summary": {
    "total_days": 22,
    "present_days": 20,
    "absent_days": 1,
    "late_days": 1,
    "total_work_hours": 180.0,
    "average_work_hours": 9.0,
    "required_hours": 176.0,
    "overtime_hours": 4.0,
    "attendance_percentage": 90.9
  },
  "daily_records": [
    {
      "date": "2026-03-04",
      "check_in": "2026-03-04T09:00:00Z",
      "check_out": "2026-03-04T18:00:00Z",
      "status": "present",
      "work_hours": 9.0
    }
  ]
}
```

**Permission Required:** All authenticated users

### 5. Get Attendance Settings

**Endpoint:** `GET /api/v1/attendance/settings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "check_in_start_time": "09:00:00",
  "check_in_end_time": "10:00:00",
  "late_grace_minutes": 15,
  "early_checkout_limit": "17:00:00"
}
```

---

### Organization Endpoints

### 1. Get Organization Overview

**Endpoint:** `GET /api/v1/organization/overview/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "organization": {
    "id": "org-id",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active",
    "timezone": "UTC"
  },
  "stats": {
    "total_users": 25,
    "active_users": 24,
    "total_roles": 4,
    "pending_invitations": 3
  }
}
```

**Permission Required:** Tenant Admin or HR

### 2. Get Organization Settings

**Endpoint:** `GET /api/v1/organization/settings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Response (200 OK):**
```json
{
  "id": "org-id",
  "name": "Acme Corporation",
  "slug": "acme",
  "status": "active",
  "timezone": "UTC",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false
}
```

**Permission Required:** Tenant Admin

### 3. Update Organization Settings

**Endpoint:** `PATCH /api/v1/organization/settings/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
Host: {{tenant_host}}
```

**Body:**
```json
{
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22
}
```

**Response (200 OK):**
```json
{
  "id": "org-id",
  "name": "Acme Corporation",
  "slug": "acme",
  "status": "active",
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22
}
```

**Permission Required:** Tenant Admin

---

### Audit Log Endpoints

### 1. List Audit Logs

**Endpoint:** `GET /api/v1/audit/`

**Headers:**
```
Authorization: Bearer {{access_token}}
Host: {{tenant_host}}
```

**Query Parameters:**
- `user_id` (optional): Filter by user
- `action` (optional): Filter by action (e.g., `user.created`, `user.updated`)
- `target_model` (optional): Filter by target model (e.g., `User`, `Role`)
- `date_from` (optional): Filter by date range start
- `date_to` (optional): Filter by date range end
- `page` (optional): Page number

**Response (200 OK):**
```json
{
  "count": 100,
  "results": [
    {
      "id": "audit-id-1",
      "user": {
        "id": "user-id-1",
        "email": "admin@acme.com"
      },
      "action": "user.created",
      "target_model": "User",
      "target_id": "new-user-id",
      "ip_address": "127.0.0.1",
      "meta": {
        "created_email": "john.doe@acme.com"
      },
      "timestamp": "2026-03-04T10:00:00.000000Z"
    }
  ]
}
```

**Permission Required:** Tenant Admin

---

## Testing Workflow

### Recommended Testing Order

1. **Authentication Flow**
   - Login → Get access/refresh tokens
   - Get Current User → Verify user info
   - Refresh Token → Test token refresh
   - Change Password → Test password update
   - Logout → Test token blacklisting

2. **User Management** (as Admin)
   - List Users
   - Create User
   - Get User Details
   - Update User
   - Delete User

3. **Role Management** (as Admin)
   - List Roles
   - Create Custom Role
   - Assign Role
   - Revoke Role
   - Delete Custom Role

4. **Invitation Flow**
   - Create Invitation
   - List Invitations
   - Accept Invitation (with new account)
   - Cancel Invitation

5. **Attendance Flow**
   - Check In
   - Check Out
   - List Attendance Records
   - Get Attendance Report

6. **Organization Settings** (as Admin)
   - Get Organization Overview
   - Get Organization Settings
   - Update Organization Settings

7. **Audit Logs** (as Admin)
   - List Audit Logs with filters

---

## Common Errors & Solutions

### 1. 401 Unauthorized

**Cause:** Invalid or expired token

**Solution:** Refresh the token or login again

### 2. 403 Forbidden

**Cause:** Insufficient permissions

**Solution:** Ensure the user has the required role (HR or Admin for most endpoints)

### 3. 404 Not Found

**Cause:** Incorrect URL or tenant not found

**Solution:**
- Verify the URL is correct
- Ensure the `Host` header is set to the correct tenant domain
- Verify the tenant exists

### 4. 400 Bad Request - "Tenant account is suspended"

**Cause:** Tenant status is suspended

**Solution:** Contact platform admin to reactivate the tenant

### 5. 400 Bad Request - Validation Error

**Cause:** Invalid request data

**Solution:** Check the error response for specific field validation errors

### 6. 422 Unprocessable Entity

**Cause:** System roles cannot be created/deleted

**Solution:** Use custom role names instead of system roles (Admin, HR, Employee)

---

## Postman Collection Export

To create a Postman collection:

1. Import the above endpoints into Postman
2. Organize into folders:
   - Authentication
   - Admin (Superuser)
   - Users
   - Roles
   - Invitations
   - Attendance
   - Organization
   - Audit Logs

3. Set up collection-level variables:
   - `base_url`: `http://127.0.0.1:8000`
   - `tenant_host`: `acme.localhost`

4. Add the following collection-level script for auto-refresh:

```javascript
// Auto-refresh token if expired
if (pm.environment.get('access_token')) {
    const token = pm.environment.get('access_token');
    const tokenPayload = JSON.parse(atob(token.split('.')[1]));
    const now = Math.floor(Date.now() / 1000);

    if (tokenPayload.exp < now) {
        // Token expired, refresh it
        const refreshReq = {
            url: pm.environment.get('base_url') + '/api/v1/auth/token/refresh/',
            method: 'POST',
            header: {
                'Content-Type': 'application/json',
                'Host': pm.environment.get('tenant_host')
            },
            body: {
                mode: 'raw',
                raw: JSON.stringify({
                    refresh: pm.environment.get('refresh_token')
                })
            }
        };

        pm.sendRequest(refreshReq, (err, res) => {
            if (!err && res.code === 200) {
                const response = res.json();
                pm.environment.set('access_token', response.access);
                if (response.refresh) {
                    pm.environment.set('refresh_token', response.refresh);
                }
            }
        });
    }
}
```

---

## Complete Postman Test Script

Add this to your login request Tests tab:

```javascript
// Save tokens and user data
if (pm.response.code === 200) {
    const response = pm.response.json();

    // Save tokens
    pm.environment.set('access_token', response.access);
    pm.environment.set('refresh_token', response.refresh);

    // Save user data
    pm.environment.set('user_id', response.user.id);
    pm.environment.set('user_email', response.user.email);
    pm.environment.set('user_name', `${response.user.first_name} ${response.user.last_name}`);
    pm.environment.set('is_tenant_admin', response.user.is_tenant_admin);
    pm.environment.set('is_superuser', response.user.is_superuser);

    // Save roles
    const roles = response.user.roles.map(r => r.name);
    pm.environment.set('user_roles', roles.join(','));

    console.log('Logged in as:', response.user.email);
    console.log('Roles:', roles);
}

// Test assertions
pm.test('Status code is 200', () => {
    pm.response.to.have.status(200);
});

pm.test('Response has access token', () => {
    pm.expect(pm.response.json()).to.have.property('access');
});

pm.test('Response has user data', () => {
    pm.expect(pm.response.json()).to.have.property('user');
});
```

---

This completes the Postman guide. Save this file for reference and import the endpoints into your Postman collection.
