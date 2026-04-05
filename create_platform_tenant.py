"""
Create the Platform Tenant with Platform Superuser.

This creates a special "platform" tenant containing platform superusers
who can manage all tenants in the system.

Usage: python create_platform_tenant.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from tenants.models import Organization, Domain
from django_tenants.utils import tenant_context

def create_platform_tenant():
    """Create the platform tenant with superuser."""
    print("=" * 60)
    print("CREATE PLATFORM TENANT")
    print("=" * 60)

    # Default credentials
    email = "superadmin@platform.local"
    password = "PlatformAdmin123!"
    first_name = "Platform"
    last_name = "Superuser"

    # Check if platform tenant exists
    existing = Organization.objects.filter(slug='platform').first()
    if existing:
        print(f"[INFO] Platform tenant already exists: {existing.name}")
        org = existing
    else:
        # Create platform organization
        org = Organization.objects.create(
            name='Platform Management',
            slug='platform',
            status='active'
        )

        # Create domain
        Domain.objects.create(
            domain='platform.localhost',
            tenant=org,
            is_primary=True
        )

        print(f"[CREATED] Platform tenant: {org.name} (slug: {org.slug})")

    # Create platform superuser
    with tenant_context(org):
        from accounts.models import User, Role, UserRole

        # Create system roles
        roles_data = [
            {'name': 'Platform Superuser', 'description': 'Can manage all tenants', 'is_system_role': True},
            {'name': 'Admin', 'description': 'Tenant administrator', 'is_system_role': True},
            {'name': 'HR', 'description': 'HR Manager', 'is_system_role': True},
            {'name': 'HR Manager', 'description': 'Senior HR Manager', 'is_system_role': True},
            {'name': 'Employee', 'description': 'Regular employee', 'is_system_role': True},
        ]

        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={
                    'description': role_data['description'],
                    'is_system_role': role_data['is_system_role']
                }
            )
            if created:
                print(f"[CREATED] Role: {role.name}")

        # Get or create platform superuser
        user = User.objects.filter(email=email).first()
        if user:
            print(f"\n[INFO] User {email} already exists")
            # Make sure it's a superuser
            user.is_superuser = True
            user.is_tenant_admin = True
            user.is_staff = True
            user.save()
            print(f"[UPDATED] User promoted to platform superuser")
        else:
            # Create platform superuser
            user = User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            print(f"\n[CREATED] Platform superuser: {email}")

        # Assign Platform Superuser role
        platform_role = Role.objects.get(name='Platform Superuser')
        UserRole.objects.get_or_create(user=user, role=platform_role)
        print(f"[ASSIGNED] Role: Platform Superuser")

    print("\n" + "=" * 60)
    print("PLATFORM TENANT SETUP COMPLETE")
    print("=" * 60)
    print(f"Tenant Slug: {org.slug}")
    print(f"Domain: platform.localhost")
    print(f"Platform Superuser: {email}")
    print(f"Password: {password}")
    print("=" * 60)
    print("\nIMPORTANT:")
    print("1. Use X-Tenant-ID: platform for platform management APIs")
    print("2. Platform superuser can access all tenant data")
    print("3. Only platform superusers can create new tenants")
    print("\nLogin with platform tenant:")
    print(f"  X-Tenant-ID: platform")
    print(f"  Email: {email}")
    print(f"  Password: {password}")

if __name__ == '__main__':
    create_platform_tenant()
