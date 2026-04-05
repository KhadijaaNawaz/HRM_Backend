# Platform Superuser and Multi-Tenant Architecture Guide

## Architecture Overview

After migrating `accounts` from TENANT_APPS to SHARED_APPS, the system now supports:

1. **Platform Superusers** (in public schema, tenant=null)
   - Can create new tenants
   - Can create other platform superusers
   - Can access all tenant data
   - Manage the entire platform

2. **Tenant Admins** (associated with a specific tenant)
   - Full access within their tenant
   - Can manage users, roles, attendance, leaves in their tenant
   - Cannot access other tenants' data

3. **Regular Users** (associated with a specific tenant)
   - Limited access within their tenant
   - Can access own data only

## Database Structure

```
Public Schema (Shared):
├── tenants (Organization, Domain)
├── accounts (User, Role, UserRole)  ← Now in SHARED_APPS!
│   └── User.tenant  ← FK to Organization (null for platform superusers)
└── django.contrib tables

Each Tenant Schema:
├── attendance
├── leaves
├── audit_logs
├── invitations
└── notifications
```

## User Types and Permissions

### Platform Superuser
```python
user.is_superuser = True
user.tenant = None  # No tenant association
```

**Capabilities:**
- Create new tenants via `/api/v1/admin/` or admin scripts
- Create other platform superusers
- View and manage all tenant data
- Access platform admin endpoints without X-Tenant-ID header

### Tenant Admin
```python
user.is_tenant_admin = True
user.tenant = <Organization instance>
user.is_superuser = False
```

**Capabilities:**
- Full access within their tenant
- Create and manage tenant users
- Manage roles, attendance, leaves
- Cannot access other tenants

### Regular User
```python
user.is_tenant_admin = False
user.is_superuser = False
user.tenant = <Organization instance>
```

**Capabilities:**
- Access own data only
- Create leave requests
- View own attendance
- Manage own profile

## Setup Instructions

### Step 1: Apply Migrations

```bash
# Apply the migration that adds tenant field to User
python manage.py migrate_schemas --shared
```

### Step 2: Migrate Existing Users (If Any)

If you have existing data from before this change:

```bash
# Migrate existing users from tenant schemas to shared table
python manage.py shell < migrate_existing_users.py
```

### Step 3: Create Platform Superuser

```bash
# Create the first platform superuser
python manage.py shell < create_platform_superuser.py
```

Example output:
```
============================================================
CREATE PLATFORM SUPERUSER
============================================================
Enter email: superadmin@hrmsaas.com
Enter password: SuperAdmin123!
Enter first name: Super
Enter last name: Admin

============================================================
PLATFORM SUPERUSER CREATED SUCCESSFULLY
============================================================
Email: superadmin@hrmsaas.com
Name: Super Admin
Is Superuser: True
Is Tenant Admin: True
Tenant: None (None = Platform Superuser)
============================================================
```

### Step 4: Login as Platform Superuser

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "superadmin@hrmsaas.com",
    "password": "SuperAdmin123!"
  }'
```

Note: No `X-Tenant-ID` header needed for platform superuser login.

### Step 5: Create New Tenants

```bash
# Create a new tenant with tenant admin
python manage.py shell < create_tenant_with_admin.py
```

Example:
```
Organization name: Acme Corporation
Organization slug: acme
Admin email: admin@acme.com
Admin password: Admin123!
Make admin a platform superuser? (y/N): n
```

## API Usage

### Platform Admin Endpoints (No X-Tenant-ID Required)

Only platform superusers can access these:

```bash
# Create new tenant
POST /api/v1/admin/tenants/
{
  "name": "New Company",
  "slug": "newco"
}

# List all tenants
GET /api/v1/admin/tenants/

# View all users across all tenants
GET /api/v1/admin/users/
```

### Tenant-Specific Endpoints (X-Tenant-ID Required)

These endpoints filter data by tenant:

```bash
# List users in the acme tenant
GET /api/v1/users/
Headers: X-Tenant-ID: acme

# Create leave request in the acme tenant
POST /api/v1/leaves/
Headers: X-Tenant-ID: acme
```

### Platform Superuser Access

Platform superusers can access any tenant's data:

```bash
# View acme tenant's users
GET /api/v1/users/
Headers:
  X-Tenant-ID: acme
  Authorization: Bearer <platform_superuser_token>

# View newco tenant's users
GET /api/v1/users/
Headers:
  X-Tenant-ID: newco
  Authorization: Bearer <platform_superuser_token>
```

## Creating Platform Superusers

### Method 1: Django Shell Script

```bash
python manage.py shell < create_platform_superuser.py
```

### Method 2: Python Code

```python
from accounts.models import User

# Create platform superuser
superuser = User.objects.create_superuser(
    email='admin@hrmsaas.com',
    password='SecurePassword123!',
    first_name='Platform',
    last_name='Admin'
)

# Ensure tenant is None
superuser.tenant = None
superuser.save()
```

### Method 3: Django Command (if created)

```bash
python manage.py createsuperuser --tenant=null
```

## Creating Tenant Admins

### Method 1: Tenant Creation Script

```bash
python manage.py shell < create_tenant_with_admin.py
```

### Method 2: Python Code

```python
from accounts.models import User
from tenants.models import Organization

# Get or create tenant
org = Organization.objects.get(slug='acme')

# Create tenant admin
admin = User.objects.create_user(
    email='admin@acme.com',
    password='Admin123!',
    first_name='Admin',
    last_name='User',
    is_tenant_admin=True
)

# Assign to tenant
admin.tenant = org
admin.save()
```

## Security Considerations

1. **Platform Superuser Creation**
   - Only existing platform superusers can create new platform superusers
   - This prevents regular tenant admins from escalating privileges

2. **Tenant Isolation**
   - All queries automatically filter by tenant for non-superusers
   - Platform superusers can bypass tenant filtering

3. **Authentication**
   - Platform superusers authenticate without tenant context
   - Tenant users authenticate with tenant context (X-Tenant-ID header)

4. **Audit Logging**
   - All actions are logged with tenant context
   - Platform superuser actions are tracked separately

## Troubleshooting

### Issue: Users not visible after migration

**Solution:** Run the migration script:
```bash
python manage.py shell < migrate_existing_users.py
```

### Issue: Can't login as platform superuser

**Solution:** Ensure:
- User has `is_superuser=True`
- User has `tenant=None`
- Not using `X-Tenant-ID` header in request

### Issue: Tenant admin can't see users

**Solution:**
- Verify user has `is_tenant_admin=True`
- Verify user.tenant is set correctly
- Check that `X-Tenant-ID` header matches user's tenant

### Issue: Permission denied when creating tenant

**Solution:** Only platform superusers can create tenants. Verify:
- User has `is_superuser=True`
- User has `tenant=None`

## Migration Checklist

- [ ] Backup database before migration
- [ ] Move accounts to SHARED_APPS in settings.py
- [ ] Add tenant field to User model
- [ ] Create and apply migrations
- [ ] Run migrate_existing_users.py script
- [ ] Create platform superuser
- [ ] Test tenant creation
- [ ] Verify tenant isolation
- [ ] Test API endpoints with different user types
- [ ] Update documentation
