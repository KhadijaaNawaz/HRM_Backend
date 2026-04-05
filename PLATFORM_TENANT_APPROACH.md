# Platform Tenant Architecture Guide

## Concept

Instead of having users in the public schema, we use a special **"platform" tenant** that contains the platform superusers who can manage all tenants.

## Architecture

```
Public Schema:
├── tenants (Organization, Domain)
└── django.contrib tables

Platform Tenant (slug: "platform"):
├── accounts (Platform Superusers)
└── These users can manage ALL tenants

Regular Tenants (slug: "acme", "newco", etc.):
├── accounts (Regular tenant users)
├── attendance
├── leaves
└── ...other apps
```

## User Types

### 1. Platform Superuser (in "platform" tenant)
```python
User.objects.filter(tenant__slug='platform', is_superuser=True)
```
- Can create new tenants
- Can create other platform superusers
- Can access all tenant data via special APIs
- Identified by: `tenant.slug == 'platform'` AND `is_superuser == True`

### 2. Tenant Admin (in regular tenant)
```python
User.objects.filter(tenant__slug='acme', is_tenant_admin=True)
```
- Full access within their tenant
- Cannot access other tenants
- Cannot create new tenants

### 3. Regular User (in regular tenant)
- Own data only within their tenant

## Implementation

### Step 1: Create Platform Tenant

Run this script to create the platform tenant:

```bash
python manage.py shell < create_platform_tenant.py
```

This creates:
- Organization with slug="platform"
- Platform superuser (e.g., superadmin@platform.local)
- This user can access all tenant management endpoints

### Step 2: Add Platform Admin Endpoints

Create special endpoints that:
1. Authenticate platform superusers
2. Allow them to create/manage tenants
3. Access data across all tenants

### Step 3: Tenant Creation Workflow

When creating a new tenant:
1. Platform superuser creates Organization
2. System creates admin user in that tenant
3. Optionally, that admin can be promoted to platform superuser

## Benefits

1. **No complex migrations** - Works with existing architecture
2. **Clean separation** - Platform users are in their own tenant
3. **Easy to understand** - Same user model everywhere
4. **Tenant isolation still works** - Regular tenants are isolated

## Migration Path

No database migration needed! Just create the platform tenant.

## Scripts Provided

- `create_platform_tenant.py` - Creates the platform tenant with superuser
- `create_new_tenant.py` - Creates regular tenants (can be run by platform superuser)

This approach achieves the same goal with less complexity!
