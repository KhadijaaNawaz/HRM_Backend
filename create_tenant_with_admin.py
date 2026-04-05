"""
Create a new tenant with tenant admin user.

Only Platform Superusers can run this script.
Creates a new tenant organization and assigns an admin user.

Usage: python manage.py shell < create_tenant_with_admin.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from tenants.models import Organization, Domain
from accounts.models import User, Role, UserRole

def create_tenant_with_admin():
    """Create a new tenant with admin user."""
    print("=" * 60)
    print("CREATE NEW TENANT WITH ADMIN")
    print("=" * 60)

    # Get tenant details
    name = input("Organization name (default: New Company): ") or "New Company"
    slug = input("Organization slug (default: newco): ") or "newco"
    admin_email = input("Admin email (default: admin@{slug}.com): ".format(slug=slug)) or f"admin@{slug}.com"
    admin_password = input("Admin password (default: Admin123!): ") or "Admin123!"
    admin_first = input("Admin first name (default: Admin): ") or "Admin"
    admin_last = input("Admin last name (default: User): ") or "User"

    make_superuser = input("Make admin a platform superuser? (y/N): ").lower() == 'y'

    # Check if tenant exists
    existing = Organization.objects.filter(slug=slug).first()
    if existing:
        print(f"\n[ERROR] Tenant with slug '{slug}' already exists!")
        return

    # Check if user exists
    existing_user = User.objects.filter(email=admin_email).first()
    if existing_user:
        print(f"\n[ERROR] User with email '{admin_email}' already exists!")
        return

    print("\n" + "=" * 60)
    print(f"CREATING TENANT: {name}")
    print("=" * 60)

    # Create organization
    org = Organization.objects.create(
        name=name,
        slug=slug,
        status='active'
    )
    print(f"[OK] Organization created: {org.name} (slug: {org.slug})")

    # Create domain
    domain = Domain.objects.create(
        domain=f'{slug}.localhost',
        tenant=org,
        is_primary=True
    )
    print(f"[OK] Domain created: {domain.domain}")

    # Create system roles for this tenant
    print("\nCreating system roles...")
    roles_created = []
    for role_name, desc in [
        ('Admin', 'Full system administrator'),
        ('HR', 'Human Resources Manager'),
        ('HR Manager', 'Senior HR Manager'),
        ('Employee', 'Regular employee')
    ]:
        role, created = Role.objects.get_or_create(
            name=role_name,
            defaults={
                'description': desc,
                'is_system_role': True
            }
        )
        if created:
            roles_created.append(role_name)
            print(f"  [CREATED] Role: {role_name}")

    # Create admin user
    print("\nCreating admin user...")
    if make_superuser:
        admin = User.objects.create_superuser(
            email=admin_email,
            password=admin_password,
            first_name=admin_first,
            last_name=admin_last
        )
        admin.tenant = org  # Associate with tenant but also make superuser
        admin.save()
        print(f"  [CREATED] Platform Superuser: {admin_email}")
    else:
        admin = User.objects.create_user(
            email=admin_email,
            password=admin_password,
            first_name=admin_first,
            last_name=admin_last,
            is_tenant_admin=True
        )
        admin.tenant = org
        admin.save()
        print(f"  [CREATED] Tenant Admin: {admin_email}")

    # Assign Admin role
    admin_role = Role.objects.get(name='Admin')
    UserRole.objects.create(user=admin, role=admin_role)
    print(f"  [ASSIGNED] Role: Admin")

    print("\n" + "=" * 60)
    print("TENANT CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Tenant ID: {org.id}")
    print(f"Tenant Name: {org.name}")
    print(f"Tenant Slug: {org.slug}")
    print(f"Domain: {slug}.localhost")
    print(f"Admin Email: {admin_email}")
    print(f"Admin Password: {admin_password}")
    print(f"Admin Type: {'Platform Superuser' if make_superuser else 'Tenant Admin'}")
    print("=" * 60)
    print("\nTo access this tenant's API:")
    print(f"  X-Tenant-ID: {slug}")
    print(f"  or use subdomain: {slug}.localhost:8000")

if __name__ == '__main__':
    create_tenant_with_admin()
