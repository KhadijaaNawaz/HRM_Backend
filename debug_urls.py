"""
Debug script to verify URL routing and tenant resolution.
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

from django.urls import get_resolver
from django.test import Client
from django.contrib.auth import get_user_model
from tenants.models import Organization, Domain
from django_tenants.utils import tenant_context

User = get_user_model()

print("Debugging URL Routing and Tenant Resolution")
print("=" * 60)

# Check available URLs
print("\n1. Available URL Patterns:")
resolver = get_resolver()
for pattern in resolver.url_patterns:
    print(f"   - {pattern}")

# Check domains
print("\n2. Configured Domains:")
for domain in Domain.objects.all():
    print(f"   - {domain.domain} -> {domain.tenant.name} ({domain.tenant.schema_name})")

# Check organizations
print("\n3. Organizations:")
for org in Organization.objects.all():
    print(f"   - {org.name} (slug: {org.slug}, schema: {org.schema_name})")

# Test tenant resolution
print("\n4. Testing Tenant Resolution with HTTP_HOST:")
test_domains = ['acme.localhost', 'localhost', '127.0.0.1']
for domain in test_domains:
    client = Client(HTTP_HOST=domain)
    response = client.get('/api/v1/auth/me/')  # Any endpoint to test
    print(f"   Host: {domain:20} -> Status: {response.status_code}")

# Test login directly with tenant context
print("\n5. Testing Login with Direct Tenant Context:")
org = Organization.objects.get(slug="acme")
with tenant_context(org):
    # Verify we're in the correct schema
    from django.db import connection
    print(f"   Current schema: {connection.schema_name}")

    # Get a test user
    user = User.objects.get(email='admin@acme.com')
    print(f"   Found user: {user.email}")

    # Try to authenticate
    from django.contrib.auth import authenticate
    authenticated_user = authenticate(
        email='admin@acme.com',
        password='Admin123!'
    )
    if authenticated_user:
        print(f"   Authentication: SUCCESS - {authenticated_user.email}")
    else:
        print(f"   Authentication: FAILED")

print("\n" + "=" * 60)
