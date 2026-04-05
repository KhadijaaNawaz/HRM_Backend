"""
Create a Platform Superuser in the public schema.

A Platform Superuser can:
- Create new tenants
- Create new platform superusers
- Access all tenant data
- Manage the entire platform

Usage: python manage.py shell < create_platform_superuser.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from accounts.models import User

def create_platform_superuser():
    """Create a platform superuser."""
    print("=" * 60)
    print("CREATE PLATFORM SUPERUSER")
    print("=" * 60)

    email = input("Enter email (default: superadmin@hrmsaas.com): ") or "superadmin@hrmsaas.com"
    password = input("Enter password (default: SuperAdmin123!): ") or "SuperAdmin123!"
    first_name = input("Enter first name (default: Super): ") or "Super"
    last_name = input("Enter last name (default: Admin): ") or "Admin"

    # Check if user already exists
    existing = User.objects.filter(email=email).first()
    if existing:
        print(f"\n[ERROR] User with email '{email}' already exists!")
        return

    # Create platform superuser (tenant=None)
    superuser = User.objects.create_superuser(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    # Ensure tenant is None for platform superuser
    superuser.tenant = None
    superuser.save()

    print("\n" + "=" * 60)
    print("PLATFORM SUPERUSER CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"Email: {superuser.email}")
    print(f"Name: {superuser.get_full_name()}")
    print(f"Is Superuser: {superuser.is_superuser}")
    print(f"Is Tenant Admin: {superuser.is_tenant_admin}")
    print(f"Tenant: {superuser.tenant} (None = Platform Superuser)")
    print("=" * 60)
    print("\nIMPORTANT:")
    print("- Use X-Tenant-ID header is NOT needed for platform admin endpoints")
    print("- Access platform admin APIs at /api/v1/admin/")
    print("- Can create new tenants and manage all data")

if __name__ == '__main__':
    create_platform_superuser()
