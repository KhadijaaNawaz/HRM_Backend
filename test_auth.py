"""
Test authentication with proper tenant context setup.
"""
import os
import django
import sys
import json

# Setup encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django_tenants.utils import tenant_context
from django_tenants.middleware.main import TenantMainMiddleware
from tenants.models import Organization

User = get_user_model()

print("Testing Authentication with Proper Tenant Context")
print("=" * 60)

# Get test organization and user
org = Organization.objects.get(slug="acme")

with tenant_context(org):
    # Test users
    test_cases = [
        ("superadmin@hrmsaas.com", "SuperAdmin123!", "Superuser (Platform Admin)"),
        ("admin@acme.com", "Admin123!", "Tenant Admin"),
        ("hr@acme.com", "HrUser123!", "HR User"),
        ("employee@acme.com", "Employee123!", "Employee"),
    ]

    print("\nTesting Login View:")
    print("-" * 60)

    for email, password, role in test_cases:
        from accounts.views import LoginView

        # Create a request with proper tenant context
        factory = RequestFactory()
        request = factory.post(
            '/api/v1/auth/login/',
            data={'email': email, 'password': password},
            content_type='application/json'
        )

        # Set tenant in request (simulating what TenantMainMiddleware does)
        request.tenant = org
        request.META['HTTP_HOST'] = 'acme.localhost'
        request.META['SERVER_NAME'] = 'acme.localhost'

        # Call the view directly
        view = LoginView.as_view()
        response = view(request)

        # Render response if needed
        if hasattr(response, 'render'):
            response.render()

        status = "PASS" if response.status_code == 200 else "FAIL"
        print(f"\n[{status}] {role}: {email}")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = json.loads(response.content)
            print(f"   Access Token: {data.get('access', 'N/A')[:50]}...")
            print(f"   User: {data.get('user', {}).get('email')}")
            print(f"   Is Tenant Admin: {data.get('user', {}).get('is_tenant_admin')}")
            print(f"   Is Superuser: {data.get('user', {}).get('is_superuser')}")
            print(f"   Roles: {data.get('user', {}).get('roles', [])}")
        else:
            print(f"   Error: {response.content.decode()[:200]}")

print("\n" + "=" * 60)
print("Authentication Test Complete!")
print("\nTest Credentials:")
print("  Superuser: superadmin@hrmsaas.com / SuperAdmin123!")
print("  Tenant Admin: admin@acme.com / Admin123!")
print("  HR: hr@acme.com / HrUser123!")
print("  Employee: employee@acme.com / Employee123!")
print("=" * 60)
