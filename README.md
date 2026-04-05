# HRM SaaS - Multi-Tenant HR Management System

A production-ready, multi-tenant HR Management System built with Django, django-tenants, and Django REST Framework. Features schema-based tenant isolation, JWT authentication, attendance tracking, role management, and comprehensive audit logging.

## Features

- **Multi-Tenancy**: Schema-based tenant isolation using django-tenants
- **Authentication**: JWT-based auth with token blacklisting
- **User Management**: Custom user model with role-based access control
- **Attendance Tracking**: Check-in/check-out with location support
- **Invitations**: Email-based user invitations with secure tokens
- **Audit Logging**: Comprehensive audit trail for compliance
- **Organization Settings**: Configurable per-tenant settings

## Technology Stack

- Python 3.11+
- Django 4.2 LTS
- django-tenants 3.6.1
- Django REST Framework 3.15.2
- PostgreSQL 15
- Redis 7
- Celery 5.3

## Project Structure

```
hrm_saas/
├── config/              # Main project configuration
│   ├── settings.py      # Django settings with tenant config
│   ├── urls.py          # Main URL configuration
│   ├── celery.py        # Celery configuration
│   └── exceptions.py    # Custom exception handler
├── tenants/             # Public schema app (Organization/Domain models)
│   ├── models.py        # Organization and Domain models
│   ├── views.py         # Tenant admin endpoints
│   ├── serializers.py   # Tenant serializers
│   └── permissions.py   # Custom permission classes
├── accounts/            # Per-tenant: User, Role, UserRole models
├── attendance/          # Per-tenant: Attendance records
├── invitations/         # Per-tenant: Email invites
├── audit_logs/          # Per-tenant: Audit logging
├── migrations_nonatomic/ # Patched auth migrations
├── manage.py
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hrm_saas
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up PostgreSQL database**
   ```bash
   createdb hrm_saas
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate_schemas --shared
   python manage.py migrate_schemas
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Docker Installation

1. **Build and start services**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate_schemas --shared
   docker-compose exec web python manage.py migrate_schemas
   ```

3. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Creating the First Tenant

After setting up the project, create the first tenant organization via the admin API:

```bash
# Login as superuser to get access token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@platform.com",
    "password": "your_password"
  }'

# Create new tenant (replace YOUR_ACCESS_TOKEN)
curl -X POST http://localhost:8000/api/v1/admin/create-tenant/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
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

Then access the tenant API using the subdomain:

```bash
# Login as tenant admin
curl -X POST http://acme.localhost:8000/api/v1/auth/login/ \
  -H "Host: acme.localhost:8000" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "TenantAdmin123!"
  }'
```

**Note**: For local development with subdomains, add entries to `/etc/hosts`:
```
127.0.0.1 acme.localhost
127.0.0.1 techcorp.localhost
```

## API Endpoints

### Platform Admin (Superuser only)
- `POST /api/v1/admin/create-tenant/` - Create new tenant
- `GET /api/v1/admin/tenants/` - List all tenants
- `GET /api/v1/admin/tenants/{id}/` - Get tenant details
- `PUT /api/v1/admin/tenants/{id}/` - Update tenant
- `DELETE /api/v1/admin/tenants/{id}/` - Delete tenant
- `POST /api/v1/admin/tenants/{id}/activate/` - Activate tenant
- `POST /api/v1/admin/tenants/{id}/suspend/` - Suspend tenant
- `GET /api/v1/admin/tenants/{id}/users/` - List tenant users

### Authentication
- `POST /api/v1/auth/login/` - User login
- `POST /api/v1/auth/logout/` - User logout
- `POST /api/v1/auth/token/refresh/` - Refresh access token
- `GET /api/v1/auth/me/` - Get current user
- `POST /api/v1/auth/password/forgot/` - Request password reset
- `POST /api/v1/auth/password/reset/` - Reset password
- `POST /api/v1/auth/password/change/` - Change password

### User Management
- `GET /api/v1/users/` - List users
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{id}/` - Get user details
- `PATCH /api/v1/users/{id}/` - Update user
- `DELETE /api/v1/users/{id}/` - Soft delete user

### Role Management
- `GET /api/v1/roles/` - List roles
- `POST /api/v1/roles/` - Create custom role
- `GET /api/v1/roles/{id}/` - Get role details
- `PATCH /api/v1/roles/{id}/` - Update role
- `DELETE /api/v1/roles/{id}/` - Delete role
- `POST /api/v1/roles/{id}/assign/` - Assign role to user
- `POST /api/v1/roles/{id}/revoke/` - Revoke role from user

### Invitations
- `POST /api/v1/invite/` - Create invitation
- `GET /api/v1/invite/` - List invitations
- `GET /api/v1/invite/{id}/` - Get invitation details
- `POST /api/v1/invite/{id}/cancel/` - Cancel invitation
- `POST /api/v1/invite/{id}/resend/` - Resend invitation
- `POST /api/v1/invite/accept/` - Accept invitation (public)

### Organization
- `GET /api/v1/organization/overview/` - Get organization stats
- `GET /api/v1/organization/settings/` - Get organization settings
- `PUT /api/v1/organization/settings/` - Update organization settings

### Attendance
- `GET /api/v1/attendance/` - List attendance records
- `GET /api/v1/attendance/{id}/` - Get attendance details
- `POST /api/v1/attendance/checkin/` - Check in
- `POST /api/v1/attendance/checkout/` - Check out
- `GET /api/v1/attendance/my-attendance/` - Get my attendance
- `GET /api/v1/attendance/my-monthly-stats/` - Get monthly stats
- `GET /api/v1/attendance/settings/` - Get attendance settings
- `PUT /api/v1/attendance/settings/` - Update attendance settings

### Audit Logs
- `GET /api/v1/audit/` - List audit logs
- `GET /api/v1/audit/{id}/` - Get audit log details

## User Roles

| Role | Permissions |
|------|-------------|
| **Platform Superuser** | Full access to all tenants and platform admin |
| **Admin** | Full tenant management access |
| **HR Manager** | User management, attendance, invitations |
| **Employee** | Self-service attendance and profile |

## Management Commands

### Migrations
```bash
python manage.py migrate_schemas --shared  # Migrate shared apps
python manage.py migrate_schemas            # Migrate tenant apps
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Collect Static Files
```bash
python manage.py collectstatic
```

### Shell Access
```bash
python manage.py shell
```

## Environment Variables

See `.env.example` for all available environment variables.

Key variables:
- `DJANGO_SECRET_KEY` - Django secret key
- `DEBUG` - Enable debug mode
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - Database configuration
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Celery configuration
- `PUBLIC_SIGNUP_ENABLED` - Allow public tenant signup (default: False)

## Security Notes

1. **Never commit `.env` file** - Use `.env.example` as template
2. **Change `SECRET_KEY`** in production
3. **Set `DEBUG=False`** in production
4. **Use strong passwords** for database and superuser
5. **Configure `ALLOWED_HOSTS`** properly
6. **Enable HTTPS** in production
7. **Regular database backups** are essential

## License

This project is proprietary software. All rights reserved.

## Support

For issues and questions, please contact the development team.
