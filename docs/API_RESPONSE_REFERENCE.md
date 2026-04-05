# HRM SaaS API Response Documentation

Complete reference for all API responses (Success & Error cases).

---

## Table of Contents

1. [Platform Admin Endpoints](#1-platform-admin-endpoints)
2. [Authentication Endpoints](#2-authentication-endpoints)
3. [User Management Endpoints](#3-user-management-endpoints)
4. [Role Management Endpoints](#4-role-management-endpoints)
5. [Attendance Endpoints](#5-attendance-endpoints)
6. [Invitation Endpoints](#6-invitation-endpoints)
7. [Audit Log Endpoints](#7-audit-log-endpoints)
8. [Organization Endpoints](#8-organization-endpoints)
9. [Common Error Codes](#9-common-error-codes)

---

## 1. Platform Admin Endpoints

### 1.1 List All Tenants

**Endpoint:** `GET /api/v1/admin/tenants/`

**Success Response (200 OK)**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "name": "Acme Corporation",
      "slug": "acme",
      "status": "active",
      "timezone": "UTC",
      "workdays": ["mon", "tue", "wed", "thu", "fri"],
      "monthly_required_days": 22,
      "public_signup_enabled": false,
      "created_at": "2026-04-05T12:41:23.706813Z",
      "updated_at": "2026-04-05T12:41:23.706831Z",
      "schema_name": "acme"
    }
  ]
}
```

**Error Responses:**

**401 Unauthorized (Missing/Invalid Token)**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden (Not Superuser)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 1.2 Create Tenant

**Endpoint:** `POST /api/v1/admin/tenants/`

**Success Response (201 Created)**
```json
{
  "organization": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active",
    "timezone": "UTC",
    "workdays": ["mon", "tue", "wed", "thu", "fri"],
    "monthly_required_days": 22,
    "public_signup_enabled": false,
    "created_at": "2026-04-05T12:41:23.706813Z",
    "updated_at": "2026-04-05T12:41:23.706831Z"
  },
  "message": "Tenant created successfully. Please complete user setup."
}
```

**Error Responses:**

**400 Bad Request (Validation Error)**
```json
{
  "slug": [
    "A tenant with this slug already exists."
  ]
}
```

```json
{
  "organization_name": [
    "This field is required."
  ]
}
```

---

### 1.3 Activate Tenant

**Endpoint:** `POST /api/v1/admin/tenants/{id}/activate/`

**Success Response (200 OK)**
```json
{
  "message": "Tenant activated successfully"
}
```

**Error Responses:**

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

---

### 1.4 Suspend Tenant

**Endpoint:** `POST /api/v1/admin/tenants/{id}/suspend/`

**Success Response (200 OK)**
```json
{
  "message": "Tenant suspended successfully"
}
```

---

### 1.5 Delete Tenant

**Endpoint:** `DELETE /api/v1/admin/tenants/{id}/`

**Success Response (204 No Content)**

**Error Responses:**

**400 Bad Request (Cannot Delete)**
```json
{
  "error": "Cannot delete tenant with active users."
}
```

---

## 2. Authentication Endpoints

### 2.1 Login

**Endpoint:** `POST /api/v1/auth/login/`

**Success Response (200 OK)**
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
    "organization": {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "name": "Acme Corporation",
      "slug": "acme",
      "status": "active"
    }
  }
}
```

**Error Responses:**

**400 Bad Request (Invalid Credentials)**
```json
{
  "detail": "Unable to log in with provided credentials.",
  "code": "authorization"
}
```

**400 Bad Request (Disabled Account)**
```json
{
  "detail": "This user account has been disabled.",
  "code": "authorization"
}
```

**400 Bad Request (Invalid Email)**
```json
{
  "email": [
    "Enter a valid email address."
  ]
}
```

**400 Bad Request (Missing Fields)**
```json
{
  "detail": "Must include \"email\" and \"password\".",
  "code": "authorization"
}
```

**403 Forbidden (Suspended Tenant)**
```json
{
  "error": "Tenant account is suspended."
}
```

---

### 2.2 Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh/`

**Success Response (200 OK)**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses:**

**401 Unauthorized (Invalid Token)**
```json
{
  "detail": "Token is invalid or expired",
  "code": "token_not_valid"
}
```

**400 Bad Request (Invalid Refresh Token)**
```json
{
  "refresh": [
    "This field is required."
  ]
}
```

---

### 2.3 Logout

**Endpoint:** `POST /api/v1/auth/logout/`

**Success Response (200 OK)**
```json
{
  "message": "Successfully logged out."
}
```

**Error Responses:**

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 2.4 Get Current User (Me)

**Endpoint:** `GET /api/v1/auth/me/`

**Success Response (200 OK)**
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
      "is_system_role": true
    }
  ],
  "organization": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "name": "Acme Corporation",
    "slug": "acme",
    "status": "active"
  }
}
```

**Error Responses:**

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 2.5 Update Current User

**Endpoint:** `PATCH /api/v1/auth/me/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "email": "admin@acme.com",
  "first_name": "Admin",
  "last_name": "Updated",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": true,
  "is_superuser": false,
  "roles": [...],
  "organization": {...}
}
```

**Error Responses:**

**400 Bad Request**
```json
{
  "phone": [
    "Enter a valid phone number."
  ]
}
```

---

### 2.6 Change Password

**Endpoint:** `POST /api/v1/auth/change-password/`

**Success Response (200 OK)**
```json
{
  "message": "Password changed successfully."
}
```

**Error Responses:**

**400 Bad Request (Wrong Old Password)**
```json
{
  "old_password": [
    "Old password is incorrect."
  ]
}
```

**400 Bad Request (Weak Password)**
```json
{
  "new_password": [
    "This password is too short. It must contain at least 8 characters.",
    "The password is too similar to the username.",
    "This password is too common."
  ]
}
```

---

### 2.7 Forgot Password

**Endpoint:** `POST /api/v1/auth/forgot-password/`

**Success Response (200 OK)**
```json
{
  "message": "If email exists, password reset link has been sent."
}
```

**Note:** Always returns success to prevent email enumeration.

**Error Responses:**

**400 Bad Request**
```json
{
  "email": [
    "This field is required."
  ]
}
```

---

### 2.8 Reset Password

**Endpoint:** `POST /api/v1/auth/reset-password/`

**Success Response (200 OK)**
```json
{
  "message": "Password reset successful."
}
```

**Error Responses:**

**400 Bad Request (Invalid Token)**
```json
{
  "error": "Invalid or expired token."
}
```

**400 Bad Request (Invalid Reset Link)**
```json
{
  "error": "Invalid reset link."
}
```

---

## 3. User Management Endpoints

### 3.1 List Users

**Endpoint:** `GET /api/v1/users/`

**Success Response (200 OK)**
```json
{
  "count": 3,
  "next": "http://api.example.com/api/v1/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "email": "admin@acme.com",
      "first_name": "Admin",
      "last_name": "User",
      "full_name": "Admin User",
      "phone": "+1234567890",
      "is_active": true,
      "is_tenant_admin": true,
      "profile_picture": null,
      "date_joined": "2026-04-05T12:41:23.706813Z",
      "last_login": "2026-04-05T14:52:17.222004Z",
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
      "user_roles": [
        {
          "id": "85efe29b-baf8-4d50-9a29-f0606a7e3b86",
          "role": {
            "id": "d9870c08-6df3-43ea-bc5a-2d0a77b8c93c",
            "name": "Admin",
            "description": "Tenant administrator with full access within the tenant organization",
            "is_system_role": true,
            "created_at": "2026-03-03T22:11:43.930978Z",
            "updated_at": "2026-03-03T22:11:43.930991Z"
          },
          "assigned_at": "2026-03-03T22:13:41.591400Z"
        }
      ]
    }
  ]
}
```

**Error Responses:**

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden (Employee accessing other users)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 3.2 Create User

**Endpoint:** `POST /api/v1/users/`

**Success Response (201 Created)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "email": "newuser@acme.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": false,
  "profile_picture": null,
  "date_joined": "2026-04-05T12:41:23.706813Z",
  "last_login": null,
  "roles": [
    {
      "id": "5fe5e8a2-4b6e-47e6-93f6-3949aeaf9f7f",
      "name": "Employee",
      "description": "Regular employee with access to own attendance and profile",
      "is_system_role": true
    }
  ]
}
```

**Error Responses:**

**400 Bad Request (Duplicate Email)**
```json
{
  "email": [
    "user with this email already exists."
  ]
}
```

**400 Bad Request (Validation Errors)**
```json
{
  "password": [
    "This field is required."
  ],
  "first_name": [
    "This field is required."
  ],
  "email": [
    "Enter a valid email address."
  ]
}
```

**400 Bad Request (Weak Password)**
```json
{
  "password": [
    "This password is too short. It must contain at least 8 characters.",
    "The password is too common."
  ]
}
```

**403 Forbidden (Not HR/Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 3.3 Get User Details

**Endpoint:** `GET /api/v1/users/{id}/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "email": "admin@acme.com",
  "first_name": "Admin",
  "last_name": "User",
  "full_name": "Admin User",
  "phone": "+1234567890",
  "is_active": true,
  "is_tenant_admin": true,
  "profile_picture": null,
  "date_joined": "2026-04-05T12:41:23.706813Z",
  "last_login": "2026-04-05T14:52:17.222004Z",
  "roles": [...],
  "user_roles": [...]
}
```

**Error Responses:**

**403 Forbidden (Accessing other user as Employee)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

---

### 3.4 Update User

**Endpoint:** `PATCH /api/v1/users/{id}/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "email": "admin@acme.com",
  "first_name": "Admin",
  "last_name": "Updated",
  "phone": "+9876543210",
  "is_active": true,
  "is_tenant_admin": true,
  "profile_picture": null,
  "date_joined": "2026-04-05T12:41:23.706813Z",
  "last_login": "2026-04-05T14:52:17.222004Z",
  "roles": [...],
  "user_roles": [...]
}
```

**Error Responses:**

**400 Bad Request**
```json
{
  "email": [
    "user with this email already exists."
  ]
}
```

**403 Forbidden**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

---

### 3.5 Delete User (Soft Delete)

**Endpoint:** `DELETE /api/v1/users/{id}/`

**Success Response (204 No Content)**

**Error Responses:**

**403 Forbidden (Not Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

---

## 4. Role Management Endpoints

### 4.1 List Roles

**Endpoint:** `GET /api/v1/roles/`

**Success Response (200 OK)**
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "d9870c08-6df3-43ea-bc5a-2d0a77b8c93c",
      "name": "Admin",
      "description": "Tenant administrator with full access within the tenant organization",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.930978Z",
      "updated_at": "2026-03-03T22:11:43.930991Z"
    },
    {
      "id": "cac5bf03-7c59-4818-98e2-2d4f2f2d6b8b",
      "name": "HR",
      "description": "HR user with access to user management and attendance tracking",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.934053Z",
      "updated_at": "2026-03-03T22:11:43.934064Z"
    },
    {
      "id": "5fe5e8a2-4b6e-47e6-93f6-3949aeaf9f7f",
      "name": "Employee",
      "description": "Regular employee with access to own attendance and profile",
      "is_system_role": true,
      "created_at": "2026-03-03T22:11:43.935654Z",
      "updated_at": "2026-03-03T22:11:43.935664Z"
    }
  ]
}
```

---

### 4.2 Create Role

**Endpoint:** `POST /api/v1/roles/`

**Success Response (201 Created)**
```json
{
  "id": "12b9bd15-8cdd-4887-ba47-97ada4c26b98",
  "name": "Manager",
  "description": "Department manager with full access to department resources",
  "is_system_role": false,
  "created_at": "2026-04-05T12:41:23.706813Z",
  "updated_at": "2026-04-05T12:41:23.706831Z"
}
```

**Error Responses:**

**400 Bad Request (Duplicate Name)**
```json
{
  "name": [
    "role with this name already exists."
  ]
}
```

**400 Bad Request (System Role)**
```json
{
  "name": [
    "Cannot create system role \"Admin\"."
  ]
}
```

**403 Forbidden (Not Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 4.3 Assign Role to User

**Endpoint:** `POST /api/v1/roles/{id}/assign/`

**Success Response (200 OK)**
```json
{
  "message": "Role Admin assigned to admin@acme.com"
}
```

**Error Responses:**

**400 Bad Request (Already Has Role)**
```json
{
  "error": "User already has this role."
}
```

**400 Bad Request (Missing user_id)**
```json
{
  "user_id": [
    "This field is required."
  ]
}
```

**403 Forbidden (Not Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found (User Not Found)**
```json
{
  "error": "User not found."
}
```

---

### 4.4 Revoke Role from User

**Endpoint:** `POST /api/v1/roles/{id}/revoke/`

**Success Response (200 OK)**
```json
{
  "message": "Role Admin revoked from admin@acme.com"
}
```

**Error Responses:**

**400 Bad Request (User Doesn't Have Role)**
```json
{
  "error": "User does not have this role."
}
```

**404 Not Found**
```json
{
  "error": "User not found."
}
```

---

### 4.5 Delete Role

**Endpoint:** `DELETE /api/v1/roles/{id}/`

**Success Response (204 No Content)**

**Error Responses:**

**400 Bad Request (System Role)**
```json
{
  "detail": "System roles cannot be deleted."
}
```

**403 Forbidden (Not Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 5. Attendance Endpoints

### 5.1 List Attendance Records

**Endpoint:** `GET /api/v1/attendance/`

**Success Response (200 OK)**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "user": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "date": "2026-04-05",
      "checkin_time": "2026-04-05T09:00:00Z",
      "checkout_time": "2026-04-05T17:00:00Z",
      "notes": "Working from office",
      "location": {
        "latitude": 40.7128,
        "longitude": -74.006
      },
      "status": "present",
      "hours_worked": 8.0,
      "created_at": "2026-04-05T09:00:00Z",
      "updated_at": "2026-04-05T17:00:00Z"
    }
  ]
}
```

**Error Responses:**

**403 Forbidden (Employee viewing others)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 5.2 Check In

**Endpoint:** `POST /api/v1/attendance/checkin/`

**Success Response (201 Created)**
```json
{
  "attendance_id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "timestamp": "2026-04-05T09:00:00Z",
  "message": "Checked in successfully"
}
```

**Error Responses:**

**400 Bad Request (Already Checked In)**
```json
{
  "error": "Already checked in today.",
  "attendance_id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "checkin_time": "2026-04-05T09:00:00Z"
}
```

---

### 5.3 Check Out

**Endpoint:** `POST /api/v1/attendance/checkout/`

**Success Response (200 OK)**
```json
{
  "attendance_id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "checkin": "2026-04-05T09:00:00Z",
  "checkout": "2026-04-05T17:00:00Z",
  "hours_worked": 8.0,
  "message": "Checked out successfully"
}
```

**Error Responses:**

**400 Bad Request (No Check-in)**
```json
{
  "error": "No check-in found for today."
}
```

**400 Bad Request (Must Check In First)**
```json
{
  "error": "Must check in before checking out."
}
```

**400 Bad Request (Already Checked Out)**
```json
{
  "error": "Already checked out today.",
  "checkout_time": "2026-04-05T17:00:00Z"
}
```

---

### 5.4 My Attendance History

**Endpoint:** `GET /api/v1/attendance/my-attendance/`

**Success Response (200 OK)**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "date": "2026-04-05",
      "checkin_time": "2026-04-05T09:00:00Z",
      "checkout_time": "2026-04-05T17:00:00Z",
      "notes": "Working from office",
      "location": {
        "latitude": 40.7128,
        "longitude": -74.006
      },
      "status": "present",
      "hours_worked": 8.0
    }
  ]
}
```

**Error Responses:**

**400 Bad Request (Invalid Date Format)**
```json
{
  "error": "Invalid start_date format. Use YYYY-MM-DD."
}
```

---

### 5.5 My Monthly Stats

**Endpoint:** `GET /api/v1/attendance/my-monthly-stats/`

**Success Response (200 OK)**
```json
{
  "month": 4,
  "year": 2026,
  "total_days": 30,
  "working_days": 22,
  "present_days": 18,
  "absent_days": 4,
  "half_days": 1,
  "late_days": 2,
  "total_hours": 144.0,
  "average_hours_per_day": 8.0
}
```

**Error Responses:**

**400 Bad Request (Invalid Month)**
```json
{
  "error": "Month must be between 1 and 12."
}
```

---

### 5.6 Get Attendance Settings

**Endpoint:** `GET /api/v1/attendance/settings/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "work_start_time": "09:00",
  "work_end_time": "17:00",
  "grace_period_minutes": 15,
  "break_duration_minutes": 60,
  "overtime_enabled": true,
  "overtime_start_after_minutes": 480,
  "created_at": "2026-04-05T12:41:23.706813Z",
  "updated_at": "2026-04-05T12:41:23.706831Z"
}
```

---

### 5.7 Update Attendance Settings

**Endpoint:** `PUT /api/v1/attendance/settings/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "work_start_time": "09:00",
  "work_end_time": "17:00",
  "grace_period_minutes": 15,
  "break_duration_minutes": 60,
  "overtime_enabled": true,
  "overtime_start_after_minutes": 480,
  "created_at": "2026-04-05T12:41:23.706813Z",
  "updated_at": "2026-04-05T14:52:17.222004Z"
}
```

**Error Responses:**

**403 Forbidden (Not Admin)**
```json
{
  "error": "Only tenant admins can update attendance settings."
}
```

---

## 6. Invitation Endpoints

### 6.1 List Invitations

**Endpoint:** `GET /api/v1/invite/`

**Success Response (200 OK)**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "email": "newuser@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role_names": ["Employee"],
      "status": "pending",
      "invited_by": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "created_at": "2026-04-05T12:41:23.706813Z",
      "updated_at": "2026-04-05T12:41:23.706831Z",
      "expires_at": "2026-04-08T12:41:23.706813Z",
      "accepted_at": null
    }
  ]
}
```

**Error Responses:**

**403 Forbidden (Not HR/Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 6.2 Create Invitation

**Endpoint:** `POST /api/v1/invite/`

**Success Response (201 Created)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role_names": ["Employee"],
  "status": "pending",
  "invited_by": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "created_at": "2026-04-05T12:41:23.706813Z",
  "updated_at": "2026-04-05T12:41:23.706831Z",
  "expires_at": "2026-04-08T12:41:23.706813Z",
  "accepted_at": null
}
```

**Error Responses:**

**400 Bad Request (Duplicate Email)**
```json
{
  "email": [
    "Invitation with this email already exists."
  ]
}
```

**403 Forbidden (Not HR/Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 6.3 Cancel Invitation

**Endpoint:** `POST /api/v1/invite/{id}/cancel/`

**Success Response (200 OK)**
```json
{
  "message": "Invitation cancelled successfully."
}
```

**Error Responses:**

**400 Bad Request (Not Pending)**
```json
{
  "error": "Only pending invitations can be cancelled."
}
```

**400 Bad Request (Not Creator)**
```json
{
  "error": "You can only cancel your own invitations."
}
```

**403 Forbidden**
```json
{
  "error": "Only tenant admins can cancel any invitation."
}
```

---

### 6.4 Resend Invitation

**Endpoint:** `POST /api/v1/invite/{id}/resend/`

**Success Response (200 OK)**
```json
{
  "message": "Invitation email resent successfully."
}
```

**Error Responses:**

**400 Bad Request (Not Pending)**
```json
{
  "error": "Only pending invitations can be resent."
}
```

---

### 6.5 Accept Invitation (Public)

**Endpoint:** `POST /api/v1/invite/accept/`

**Success Response (201 Created)**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "email": "newuser@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Error Responses:**

**400 Bad Request (Invalid Token)**
```json
{
  "token": [
    "Invalid token."
  ]
}
```

**400 Bad Request (Expired)**
```json
{
  "detail": "Invitation has expired."
}
```

**400 Bad Request (Already Accepted)**
```json
{
  "detail": "Invitation has already been accepted."
}
```

**400 Bad Request (Weak Password)**
```json
{
  "password": [
    "This password is too short. It must contain at least 8 characters."
  ]
}
```

---

## 7. Audit Log Endpoints

### 7.1 List Audit Logs

**Endpoint:** `GET /api/v1/audit/`

**Success Response (200 OK)**
```json
{
  "count": 50,
  "next": "http://api.example.com/api/v1/audit/?page=2",
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "user": {
        "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
        "email": "admin@acme.com"
      },
      "action": "user.login",
      "target_model": "User",
      "target_id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "meta": {
        "user_agent": "Mozilla/5.0...",
        "login_method": "email"
      },
      "ip_address": "192.168.1.1",
      "timestamp": "2026-04-05T14:52:17.222004Z"
    }
  ]
}
```

**Error Responses:**

**403 Forbidden (Not Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## 8. Organization Endpoints

### 8.1 Get Organization Overview

**Endpoint:** `GET /api/v1/organization/overview/`

**Success Response (200 OK)**
```json
{
  "total_users": 25,
  "active_users": 20,
  "roles_count": 5,
  "attendance_today": {
    "total": 25,
    "present": 18,
    "pending": 7
  }
}
```

**Error Responses:**

**403 Forbidden (Not HR/Admin)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 8.2 Get Organization Settings

**Endpoint:** `GET /api/v1/organization/settings/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "name": "Acme Corporation",
  "slug": "acme",
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false,
  "created_at": "2026-04-05T12:41:23.706813Z",
  "updated_at": "2026-04-05T12:41:23.706831Z"
}
```

---

### 8.3 Update Organization Settings

**Endpoint:** `PUT /api/v1/organization/settings/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "name": "Acme Corporation",
  "slug": "acme",
  "timezone": "America/New_York",
  "workdays": ["mon", "tue", "wed", "thu", "fri"],
  "monthly_required_days": 22,
  "public_signup_enabled": false,
  "created_at": "2026-04-05T12:41:23.706813Z",
  "updated_at": "2026-04-05T14:52:17.222004Z"
}
```

**Error Responses:**

**400 Bad Request (Invalid Workdays)**
```json
{
  "workdays": [
    "Invalid workday. Must be one of: mon, tue, wed, thu, fri, sat, sun"
  ]
}
```

**403 Forbidden (Not Admin)**
```json
{
  "error": "Only tenant admins can update organization settings."
}
```

---

## 9. Leave Management Endpoints

### 9.1 List Leaves

**Endpoint:** `GET /api/v1/leaves/`

**Success Response (200 OK)**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "employee": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "employee_email": "john.doe@acme.com",
      "employee_name": "John Doe",
      "leave_type": "casual",
      "leave_type_display": "Casual Leave",
      "start_date": "2026-04-10",
      "end_date": "2026-04-12",
      "reason": "Personal work",
      "status": "pending",
      "status_display": "Pending",
      "approved_by": null,
      "approved_at": null,
      "approver_name": null,
      "rejected_by": null,
      "rejected_at": null,
      "rejecter_name": null,
      "rejection_reason": "",
      "days": 3,
      "is_pending": true,
      "is_approved": false,
      "is_rejected": false,
      "is_cancelled": false,
      "created_at": "2026-04-05T12:41:23.706813Z",
      "updated_at": "2026-04-05T12:41:23.706831Z"
    }
  ]
}
```

**Error Responses:**

**403 Forbidden (Employee viewing others)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 9.2 Create Leave Request

**Endpoint:** `POST /api/v1/leaves/`

**Success Response (201 Created)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "employee": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "leave_type": "casual",
  "start_date": "2026-04-10",
  "end_date": "2026-04-12",
  "reason": "Personal work",
  "status": "pending",
  "days": 3,
  "is_pending": true,
  "created_at": "2026-04-05T12:41:23.706813Z"
}
```

**Error Responses:**

**400 Bad Request (Overlapping Leaves)**
```json
{
  "error": "You have overlapping leave requests"
}
```

**400 Bad Request (Insufficient Balance)**
```json
{
  "error": "Insufficient Casual leave balance"
}
```

**400 Bad Request (Invalid Date Range)**
```json
{
  "end_date": [
    "End date must be after or equal to start date."
  ]
}
```

**400 Bad Request (Past Date)**
```json
{
  "start_date": [
    "Start date cannot be in the past."
  ]
}
```

---

### 9.3 Get Leave Details

**Endpoint:** `GET /api/v1/leaves/{id}/`

**Success Response (200 OK)**
```json
{
  "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "employee": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "employee_email": "john.doe@acme.com",
  "employee_name": "John Doe",
  "leave_type": "casual",
  "leave_type_display": "Casual Leave",
  "start_date": "2026-04-10",
  "end_date": "2026-04-12",
  "reason": "Personal work",
  "status": "approved",
  "status_display": "Approved",
  "approved_by": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
  "approved_at": "2026-04-05T14:52:17.222004Z",
  "approver_name": "Admin User",
  "days": 3,
  "is_pending": false,
  "is_approved": true,
  "created_at": "2026-04-05T12:41:23.706813Z",
  "updated_at": "2026-04-05T14:52:17.222004Z"
}
```

**Error Responses:**

**403 Forbidden (Not Owner)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found**
```json
{
  "detail": "Not found."
}
```

---

### 9.4 Approve Leave

**Endpoint:** `POST /api/v1/leaves/{id}/approve/`

**Success Response (200 OK)**
```json
{
  "message": "Leave request approved successfully.",
  "leave": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "status": "approved",
    "approved_by": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "approved_at": "2026-04-05T14:52:17.222004Z",
    "leave_type": "casual",
    "days": 3
  }
}
```

**Error Responses:**

**400 Bad Request (Not Pending)**
```json
{
  "error": "Only pending leaves can be approved. Current status: Approved"
}
```

**403 Forbidden (Not HR/Admin)**
```json
{
  "error": "Only HR and Admin users can approve leaves."
}
```

---

### 9.5 Reject Leave

**Endpoint:** `POST /api/v1/leaves/{id}/reject/`

**Request Body:**
```json
{
  "reason": "Insufficient staff coverage for these dates."
}
```

**Success Response (200 OK)**
```json
{
  "message": "Leave request rejected successfully.",
  "leave": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "status": "rejected",
    "rejected_by": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "rejected_at": "2026-04-05T14:52:17.222004Z",
    "rejection_reason": "Insufficient staff coverage for these dates."
  }
}
```

**Error Responses:**

**400 Bad Request (Missing Reason)**
```json
{
  "reason": [
    "This field is required."
  ]
}
```

**400 Bad Request (Not Pending)**
```json
{
  "error": "Only pending leaves can be rejected. Current status: Rejected"
}
```

**403 Forbidden (Not HR/Admin)**
```json
{
  "error": "Only HR and Admin users can reject leaves."
}
```

---

### 9.6 Cancel Leave

**Endpoint:** `POST /api/v1/leaves/{id}/cancel/`

**Success Response (200 OK)**
```json
{
  "message": "Leave cancelled successfully.",
  "leave": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "status": "cancelled",
    "is_cancelled": true
  }
}
```

**Error Responses:**

**400 Bad Request (Cannot Cancel)**
```json
{
  "error": "Cannot cancel rejected or already cancelled leaves."
}
```

**403 Forbidden (Not Owner)**
```json
{
  "error": "You can only cancel your own leaves."
}
```

---

### 9.7 My Leaves

**Endpoint:** `GET /api/v1/leaves/my-leaves/`

**Query Parameters:**
- `status`: Filter by status (pending, approved, rejected, cancelled)
- `year`: Filter by year (e.g., 2026)
- `leave_type`: Filter by leave type (casual, sick, earned, etc.)

**Success Response (200 OK)**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "leave_type": "casual",
      "leave_type_display": "Casual Leave",
      "start_date": "2026-04-10",
      "end_date": "2026-04-12",
      "reason": "Personal work",
      "status": "pending",
      "status_display": "Pending",
      "days": 3,
      "created_at": "2026-04-05T12:41:23.706813Z"
    }
  ]
}
```

---

### 9.8 Leave Summary

**Endpoint:** `GET /api/v1/leaves/summary/`

**Query Parameters:**
- `year`: Filter by year (default: current year)
- `month`: Filter by month (1-12)

**Success Response (200 OK)**
```json
{
  "year": 2026,
  "month": null,
  "total_leaves": 50,
  "pending_leaves": 5,
  "approved_leaves": 35,
  "rejected_leaves": 8,
  "cancelled_leaves": 2,
  "by_type": {
    "casual": {
      "name": "Casual Leave",
      "count": 20
    },
    "sick": {
      "name": "Sick Leave",
      "count": 15
    },
    "earned": {
      "name": "Earned Leave",
      "count": 10
    }
  },
  "this_month_pending": 2,
  "this_month_approved": 8,
  "this_month_rejected": 1,
  "upcoming_leaves": 12
}
```

**Error Responses:**

**403 Forbidden (Not HR/Admin)**
```json
{
  "error": "Only HR and Admin users can access leave summary."
}
```

---

### 9.9 Leave Balance

**Endpoint:** `GET /api/v1/leaves/balance/`

**Query Parameters:**
- `year`: Filter by year (default: current year)
- `leave_type`: Filter by leave type

**Success Response (200 OK)**
```json
{
  "year": 2026,
  "employee_email": "john.doe@acme.com",
  "balances": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "employee": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "employee_email": "john.doe@acme.com",
      "employee_name": "John Doe",
      "leave_type": "casual",
      "leave_type_display": "Casual Leave",
      "year": 2026,
      "total_days": 12,
      "used_days": 5,
      "balance_days": 7,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-04-05T12:41:23.706813Z"
    }
  ]
}
```

---

### 9.10 List Leave Balances (Admin)

**Endpoint:** `GET /api/v1/leaves/balances/`

**Success Response (200 OK)**
```json
{
  "count": 25,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "employee": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "employee_email": "john.doe@acme.com",
      "employee_name": "John Doe",
      "leave_type": "casual",
      "leave_type_display": "Casual Leave",
      "year": 2026,
      "total_days": 12,
      "used_days": 5,
      "balance_days": 7
    }
  ]
}
```

---

## 10. Notification Endpoints

### 10.1 List Notifications

**Endpoint:** `GET /api/v1/notifications/`

**Success Response (200 OK)**
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "user": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "user_email": "john.doe@acme.com",
      "user_name": "John Doe",
      "title": "Leave Request Approved",
      "message": "Your Casual leave from April 10 to April 12 has been approved by Admin User.",
      "notification_type": "leave_approved",
      "notification_type_display": "Leave Approved",
      "is_read": false,
      "action_url": "/leaves/5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
      "action_text": "View Leave",
      "metadata": {
        "leave_id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
        "approved_by": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2"
      },
      "created_at": "2026-04-05T14:52:17.222004Z",
      "read_at": null
    }
  ]
}
```

---

### 10.2 Mark Notification as Read

**Endpoint:** `POST /api/v1/notifications/{id}/read/`

**Success Response (200 OK)**
```json
{
  "message": "Notification marked as read.",
  "notification": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "is_read": true,
    "read_at": "2026-04-05T15:30:00.000000Z",
    "title": "Leave Request Approved",
    "message": "Your Casual leave from April 10 to April 12 has been approved by Admin User."
  }
}
```

**Error Responses:**

**403 Forbidden (Not Owner)**
```json
{
  "error": "You can only manage your own notifications."
}
```

---

### 10.3 Mark Notification as Unread

**Endpoint:** `POST /api/v1/notifications/{id}/unread/`

**Success Response (200 OK)**
```json
{
  "message": "Notification marked as unread.",
  "notification": {
    "id": "5375cf8f-b9eb-40b6-8c91-0f614507f1e2",
    "is_read": false,
    "read_at": null
  }
}
```

---

### 10.4 Mark All as Read

**Endpoint:** `POST /api/v1/notifications/read-all/`

**Success Response (200 OK)**
```json
{
  "message": "Marked 15 notifications as read.",
  "updated_count": 15
}
```

---

### 10.5 Get Unread Count

**Endpoint:** `GET /api/v1/notifications/unread-count/`

**Success Response (200 OK)**
```json
{
  "unread_count": 7
}
```

---

### 10.6 Clear All Read Notifications

**Endpoint:** `DELETE /api/v1/notifications/clear-all/`

**Success Response (200 OK)**
```json
{
  "message": "Deleted 8 read notifications.",
  "deleted_count": 8
}
```

---

## 11. Common Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| **200** | OK - Request successful |
| **201** | Created - Resource created successfully |
| **204** | No Content - Deletion successful |
| **400** | Bad Request - Invalid input data |
| **401** | Unauthorized - Missing or invalid authentication |
| **403** | Forbidden - Insufficient permissions |
| **404** | Not Found - Resource doesn't exist |
| **405** | Method Not Allowed - Invalid HTTP method |
| **500** | Internal Server Error - Server error |

### Common Error Response Formats

**Validation Error (400)**
```json
{
  "field_name": [
    "Error message 1",
    "Error message 2"
  ]
}
```

**Authorization Error (401)**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**Permission Error (403)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

**Not Found Error (404)**
```json
{
  "detail": "Not found."
}
```

**Server Error (500)**
```json
{
  "detail": "Internal server error. Please try again later."
}
```

---

## 12. Pagination Response Format

All list endpoints support pagination:

```json
{
  "count": 150,
  "next": "http://api.example.com/api/v1/users/?page=2",
  "previous": null,
  "results": [
    { ... },
    { ... }
  ]
}
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

---

## 13. Tenant Headers

All requests must include the tenant identifier:

**Using X-Tenant-ID Header (Recommended):**
```
X-Tenant-ID: acme
```

**Using Subdomain (Alternative):**
```
Host: acme.localhost:8000
```

---

## 14. Authentication Header Format

```
Authorization: Bearer <access_token>
```

**Example:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

*This document covers all endpoints and their possible responses. For filtering and search parameters, refer to the FILTERING_API_REFERENCE.md document.*
