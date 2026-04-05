# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django-based HRM (Human Resource Management) SaaS application with multi-tenancy support. The project uses `django-tenants` for tenant isolation and Django REST Framework for building APIs.

## Technology Stack

- **Python**: 3.13.7
- **Django**: 6.0.3
- **Multi-tenancy**: django-tenants 3.10.0
- **API Framework**: Django REST Framework 3.16.1
- **Authentication**: djangorestframework_simplejwt 5.5.1
- **Database**: PostgreSQL (psycopg2-binary 2.9.11) - SQLite configured for development

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

# Install dependencies (from pip list)
pip install Django==6.0.3 django-tenants==3.10.0 djangorestframework==3.16.1 djangorestframework_simplejwt==5.5.1 psycopg2-binary==2.9.11
```

### Django Management
```bash
# Run development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations for shared apps (public schema)
python manage.py migrate_schemas --shared

# Apply migrations for tenant apps
python manage.py migrate_schemas

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run shell
python manage.py shell
```

### Testing
```bash
# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test tenants
python manage.py test users
python manage.py test organization
python manage.py test attendance
python manage.py test roles
python manage.py test audit_logs
```

## Architecture

### Multi-Tenancy Pattern

The application uses a schema-based multi-tenancy approach via `django-tenants`:

**SHARED_APPS** (public schema):
- `django_tenants` - Multi-tenancy framework
- `tenants` - Custom tenant models (Domain, Tenant)
- Django contrib apps (auth, sessions, admin, etc.)
- `rest_framework` - API framework

**TENANT_APPS** (tenant-specific schemas):
- `users` - User management (tenant-isolated users)
- `organization` - Organization/department structures
- `attendance` - Attendance tracking and records
- `roles` - Role and permission management
- `audit_logs` - Audit trail for tenant actions

### Directory Structure

```
hrm_saas/
├── config/           # Main project configuration (settings, urls, wsgi, asgi)
├── tenants/          # Tenant and Domain models (shared app)
├── users/            # User models and authentication (tenant app)
├── organization/     # Company/organization structure (tenant app)
├── attendance/       # Attendance tracking (tenant app)
├── roles/            # Role-based access control (tenant app)
├── audit_logs/       # Audit logging (tenant app)
├── manage.py         # Django management script
└── venv/             # Virtual environment
```

### Key Architectural Notes

1. **Tenant Isolation**: All tenant-specific data is isolated at the database schema level. Each tenant gets its own PostgreSQL schema.

2. **Shared vs Tenant Models**: Models in `tenants/` app are shared across all tenants. Models in other apps are tenant-specific.

3. **Middleware Order**: When adding `django_tenants.middleware.main.TenantMainMiddleware`, it must be at the top of MIDDLEWARE list (not yet configured in current settings).

4. **Database Router**: The project uses django-tenants' database router for routing queries to appropriate schemas.

5. **Settings Module**: `config.settings` is the main settings module. Environment-specific settings should be handled via environment variables or separate settings modules.

## API Specification

The project follows a RESTful API structure with versioning (`api/v1`). See `HRM_SaaS_Complete_API.postman_collection.json` for the complete API specification.

### API Modules

1. **Platform Admin** (`/api/v1/admin/`) - Tenant management for platform superusers
   - Create/list/update/delete/activate/suspend tenants
   - View tenant users

2. **Authentication** (`/api/v1/auth/`) - JWT-based auth with refresh tokens
   - Login, logout, token refresh, current user (`/me/`)
   - Password management: forgot, reset, change

3. **User Management** (`/api/v1/users/`) - CRUD operations for tenant users
   - Users are tenant-isolated
   - Soft delete (deactivation) instead of hard delete

4. **Role Management** (`/api/v1/roles/`) - Role-based access control
   - System roles: Admin, HR, Employee (cannot be deleted)
   - Custom roles can be created
   - Assign/revoke roles from users

5. **Invitations** (`/api/v1/invite/`) - Email-based user invitations
   - Create, list, cancel invitations
   - Accept invitations with token (public endpoint)
   - Resend invitations

6. **Organization** (`/api/v1/organization/`) - Organization settings
   - Overview/stats endpoint
   - Settings: timezone, workdays, required days, public signup toggle

7. **Attendance** (`/api/v1/attendance/`) - Attendance tracking
   - Check-in/check-out with location support
   - My attendance history with date filtering
   - Monthly statistics
   - Employees see only their records; HR/Admin see all

8. **Audit Logs** (`/api/v1/audit/`) - Compliance audit trail
   - Log all tenant actions
   - Admin-only access

### Multi-Tenancy via Subdomains

- Tenants are identified via subdomain in the Host header (e.g., `acme.localhost:8000`)
- Example: `Host: acme.localhost:8000` routes to the "acme" tenant
- Platform admin endpoints use the base URL (no subdomain)

### User Roles

- **Platform Superuser** (`is_superuser=True`) - Can manage all tenants via `/api/v1/admin/`
- **Admin** - Full tenant management access
- **HR** - User and attendance management
- **Employee** - Self-service attendance only

## Important Considerations

1. **Migrations**: Always use `migrate_schemas` instead of `migrate` to handle both shared and tenant schemas.

2. **Tenant Awareness**: All tenant-app queries automatically filter by the current tenant based on the request's Host header (subdomain).

3. **Development vs Production**: Current settings use DEBUG=True with a hardcoded SECRET_KEY. These must be changed for production deployment.

4. **Middleware Configuration**: `django_tenants.middleware.main.TenantMainMiddleware` must be added at the top of MIDDLEWARE for subdomain-based tenant resolution (not yet configured).

5. **Database Router**: The project requires django-tenants' database router (`DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)`).

6. **Public Signup**: Controlled by `PUBLIC_SIGNUP_ENABLED` setting. When disabled, signup returns 403 Forbidden.
