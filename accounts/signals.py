"""
Signals for accounts app.

Handles automatic creation of default roles when migrations run.
"""

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection


@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    """
    Create default system roles after migrations.

    This creates the four default roles:
    - Superuser: Platform-level superuser (managed by Django's is_superuser)
    - Admin: Tenant administrator with full access within tenant
    - HR: HR user with access to user and attendance management
    - Employee: Regular employee with access to own attendance and profile

    NOTE: Only runs for tenant schemas, NOT the public/shared schema.
    This is because accounts is in TENANT_APPS, so its tables only exist
    in tenant schemas.
    """
    # Skip if running on public/shared schema
    if connection.schema_name == 'public' or connection.schema_name is None:
        return

    # Only run for accounts app
    if sender.name != 'accounts':
        return

    from .models import Role

    # Define default roles - 4 tier hierarchy
    default_roles = [
        {
            'name': 'Admin',
            'description': 'Tenant administrator with full access within the tenant organization',
            'is_system_role': True
        },
        {
            'name': 'HR',
            'description': 'HR user with access to user management and attendance tracking',
            'is_system_role': True
        },
        {
            'name': 'Employee',
            'description': 'Regular employee with access to own attendance and profile',
            'is_system_role': True
        }
    ]

    # Create roles if they don't exist
    for role_data in default_roles:
        Role.objects.get_or_create(
            name=role_data['name'],
            defaults={
                'description': role_data['description'],
                'is_system_role': role_data['is_system_role']
            }
        )
