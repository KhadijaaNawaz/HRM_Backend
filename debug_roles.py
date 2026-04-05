"""
Debug script to verify role assignments.
"""
import os
import django
import sys

# Setup encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from django.contrib.auth import get_user_model
from tenants.models import Organization
from django_tenants.utils import tenant_context
from accounts.models import Role, UserRole

User = get_user_model()

print("Debugging Role Assignments")
print("=" * 60)

org = Organization.objects.get(slug="acme")

with tenant_context(org):
    # Check all roles
    print("\n1. All Roles in Database:")
    for role in Role.objects.all():
        print(f"   - {role.name} (ID: {role.id})")

    # Check all UserRole records
    print("\n2. All UserRole Records:")
    user_roles = UserRole.objects.all()
    if user_roles.exists():
        for ur in user_roles:
            print(f"   - User: {ur.user.email} -> Role: {ur.role.name}")
    else:
        print("   No UserRole records found!")

    # Check each user's roles
    print("\n3. User Roles (via user.roles):")
    for user in User.objects.all():
        roles_list = list(user.roles.all())
        print(f"   - {user.email}:")
        print(f"      Direct UserRole query: {list(user.user_roles.all())}")
        print(f"      Via roles property: {roles_list}")
        print(f"      Role names: {[r.name for r in roles_list]}")

print("\n" + "=" * 60)
