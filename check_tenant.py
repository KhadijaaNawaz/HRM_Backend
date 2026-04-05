"""Check tenant setup and create domain if needed."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
django.setup()

from tenants.models import Organization, Domain

print("=== Checking Tenant Setup ===\n")

# Check domains
domains = Domain.objects.all()
print(f"Domains found: {domains.count()}")
for domain in domains:
    print(f"  - {domain.domain} -> {domain.tenant.name} (schema: {domain.tenant.schema_name})")

# Check organizations
orgs = Organization.objects.all()
print(f"\nOrganizations found: {orgs.count()}")
for org in orgs:
    print(f"  - {org.name} (slug: {org.slug}, schema: {org.schema_name})")

# Check if acme.localhost exists
try:
    acme_domain = Domain.objects.get(domain='acme.localhost')
    print(f"\nacme.localhost EXISTS!")
    print(f"   Tenant: {acme_domain.tenant.name}")
    print(f"   Schema: {acme_domain.tenant.schema_name}")
except Domain.DoesNotExist:
    print("\nacme.localhost does NOT exist!")
    print("Creating it now...")

    org = Organization.objects.get(slug='acme')
    domain = Domain.objects.create(
        domain='acme.localhost',
        tenant=org,
        is_primary=True
    )
    print(f"Created: acme.localhost -> {org.name}")
