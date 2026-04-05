"""
Create a new tenant with admin user.
Usage: python manage.py shell < create_new_tenant.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from tenants.models import Organization, Domain
from django_tenants.utils import tenant_context

def create_new_tenant():
    """Create a new tenant organization with admin user."""

    # Get tenant details from input or use defaults
    name = input("Organization name (default: New Company): ") or "New Company"
    slug = input("Organization slug (default: newco): ") or "newco"
    admin_email = input("Admin email (default: admin@{slug}.com): ".format(slug=slug)) or f"admin@{slug}.com"
    admin_password = input("Admin password (default: Admin123!): ") or "Admin123!"

    print("\n" + "=" * 60)
    print(f"CREATING TENANT: {name}")
    print("=" * 60)

    # Check if tenant exists
    existing = Organization.objects.filter(slug=slug).first()
    if existing:
        print(f"Tenant '{slug}' already exists!")
        return

    # Create organization
    org = Organization.objects.create(
        name=name,
        slug=slug,
        status='active'
    )

    # Create domain
    Domain.objects.create(
        domain=f'{slug}.localhost',
        tenant=org,
        is_primary=True
    )

    print(f"Tenant created: {org.name} (slug: {org.slug})")

    # Create admin user in tenant context
    with tenant_context(org):
        from accounts.models import User, Role, UserRole

        # Create system roles
        for role_name, desc in [
            ('Admin', 'Full system administrator'),
            ('HR', 'Human Resources Manager'),
            ('HR Manager', 'Senior HR Manager'),
            ('Employee', 'Regular employee')
        ]:
            Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': desc,
                    'is_system_role': True
                }
            )

        # Create admin user
        admin = User.objects.create_user(
            email=admin_email,
            password=admin_password,
            first_name='Admin',
            last_name='User',
            is_tenant_admin=True
        )

        # Assign Admin role
        admin_role = Role.objects.get(name='Admin')
        UserRole.objects.create(user=admin, role=admin_role)

        print(f"Admin user created: {admin_email}")
        print(f"Password: {admin_password}")

    print("\n" + "=" * 60)
    print("TENANT CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Tenant ID: {org.id}")
    print(f"Tenant Slug: {org.slug}")
    print(f"Domain: {slug}.localhost")
    print(f"Admin Email: {admin_email}")
    print(f"Use X-Tenant-ID: {slug} for API requests")
    print("=" * 60)

if __name__ == '__main__':
    create_new_tenant()
