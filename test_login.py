"""
Test script to verify the login API works correctly with tenant isolation.
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

from django.test import Client
from django.contrib.auth import get_user_model
from tenants.models import Organization
from django_tenants.utils import tenant_context

User = get_user_model()

print("Testing Login API with Tenant Isolation")
print("=" * 50)

# Get test users
org = Organization.objects.get(slug="acme")
with tenant_context(org):
    # List all users
    users = User.objects.all()
    print(f"\nTotal users in {org.schema_name}: {users.count()}")
    for user in users:
        roles = [ur.role.name for ur in user.user_roles.all()]
        print(f"  - {user.email}: is_superuser={user.is_superuser}, is_tenant_admin={user.is_tenant_admin}, roles={roles}")

# Test login for each user
test_cases = [
    ("superadmin@hrmsaas.com", "SuperAdmin123!", "Superuser (Platform Admin)"),
    ("admin@acme.com", "Admin123!", "Tenant Admin"),
    ("hr@acme.com", "HrUser123!", "HR User"),
    ("employee@acme.com", "Employee123!", "Employee"),
]

print("\n" + "=" * 50)
print("Testing Login API")
print("=" * 50)

for email, password, role in test_cases:
    client = Client(HTTP_HOST='acme.localhost')
    response = client.post(
        '/api/v1/auth/login/',
        data={'email': email, 'password': password},
        content_type='application/json'
    )

    status = "PASS" if response.status_code == 200 else "FAIL"
    print(f"\n[{status}] {role}: {email}")
    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        import json
        data = json.loads(response.content)
        print(f"   Access Token: {data.get('access', 'N/A')[:50]}...")
        print(f"   User: {data.get('user', {}).get('email')}")
        print(f"   Is Tenant Admin: {data.get('user', {}).get('is_tenant_admin')}")
        print(f"   Roles: {data.get('user', {}).get('roles', [])}")
    else:
        print(f"   Error: {response.content.decode()[:200]}")

print("\n" + "=" * 50)
print("Testing complete!")
print("=" * 50)
