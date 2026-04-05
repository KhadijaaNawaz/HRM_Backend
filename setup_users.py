"""
Setup script to create users with different roles for testing.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from tenants.models import Organization
from django_tenants.utils import tenant_context
from accounts.models import Role, UserRole

User = get_user_model()

# Switch to the acme tenant schema
org = Organization.objects.get(slug="acme")
with tenant_context(org):
    print(f"Current schema: {org.schema_name}")
    print(f"\nAvailable roles:")
    for role in Role.objects.all():
        print(f"  - {role.name}: {role.description}")

    # Check existing users
    existing_users = User.objects.all()
    print(f"\nExisting users count: {existing_users.count()}")
    if existing_users.exists():
        print("Existing users:")
        for u in existing_users:
            print(f"  - {u.email} (is_tenant_admin={u.is_tenant_admin}, is_superuser={u.is_superuser})")

    # Create a superuser (platform-level admin)
    if not User.objects.filter(email='superadmin@hrmsaas.com').exists():
        superuser = User.objects.create_superuser(
            email='superadmin@hrmsaas.com',
            password='SuperAdmin123!',
            first_name='Super',
            last_name='Admin'
        )
        print(f"\nCreated superuser: {superuser.email}")
    else:
        print("\nSuperuser already exists")

    # Create tenant admin
    admin_role = Role.objects.get(name='Admin')
    if not User.objects.filter(email='admin@acme.com').exists():
        admin_user = User.objects.create_user(
            email='admin@acme.com',
            password='Admin123!',
            first_name='Admin',
            last_name='User',
            is_tenant_admin=True
        )
        UserRole.objects.create(user=admin_user, role=admin_role)
        print(f"Created tenant admin: {admin_user.email}")
    else:
        print("Tenant admin already exists")

    # Create HR user
    hr_role = Role.objects.get(name='HR')
    if not User.objects.filter(email='hr@acme.com').exists():
        hr_user = User.objects.create_user(
            email='hr@acme.com',
            password='HrUser123!',
            first_name='HR',
            last_name='Manager'
        )
        UserRole.objects.create(user=hr_user, role=hr_role)
        print(f"Created HR user: {hr_user.email}")
    else:
        print("HR user already exists")

    # Create regular employee
    employee_role = Role.objects.get(name='Employee')
    if not User.objects.filter(email='employee@acme.com').exists():
        employee_user = User.objects.create_user(
            email='employee@acme.com',
            password='Employee123!',
            first_name='John',
            last_name='Doe'
        )
        UserRole.objects.create(user=employee_user, role=employee_role)
        print(f"Created employee: {employee_user.email}")
    else:
        print("Employee already exists")

    print("\nAll users created successfully!")
    print("\nTest credentials:")
    print("  Superuser: superadmin@hrmsaas.com / SuperAdmin123!")
    print("  Tenant Admin: admin@acme.com / Admin123!")
    print("  HR: hr@acme.com / HrUser123!")
    print("  Employee: employee@acme.com / Employee123!")
