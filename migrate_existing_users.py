"""
Migrate existing users from tenant schemas to shared accounts table.

This script handles migration when moving accounts from TENANT_APPS to SHARED_APPS.
Run this after applying the 0002_user_tenant migration.

IMPORTANT: This is a one-time migration script. Backup your database before running!

Usage: python manage.py shell < migrate_existing_users.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.db import connection
from tenants.models import Organization
from accounts.models import User, Role, UserRole

def migrate_users_from_schema(schema_name):
    """Migrate users from a specific tenant schema."""
    print(f"\n{'=' * 60}")
    print(f"MIGRATING USERS FROM TENANT: {schema_name}")
    print(f"{'=' * 60}")

    # Get the organization
    try:
        org = Organization.objects.get(schema_name=schema_name)
    except Organization.DoesNotExist:
        print(f"[ERROR] Organization with schema '{schema_name}' not found!")
        return

    # Set the search path to the tenant schema
    with connection.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema_name}, public")

        # Check if users table exists in tenant schema
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s AND table_name = 'users'
            )
        """, [schema_name])

        if not cursor.fetchone()[0]:
            print(f"[SKIP] No users table found in schema '{schema_name}'")
            return

        # Get all users from tenant schema
        cursor.execute("""
            SELECT id, email, first_name, last_name, phone,
                   is_active, is_tenant_admin, is_staff,
                   date_joined, updated_at, last_login, profile_picture
            FROM users
        """)

        users_data = cursor.fetchall()

        if not users_data:
            print(f"[SKIP] No users found in schema '{schema_name}'")
            return

        print(f"[FOUND] {len(users_data)} users in schema '{schema_name}'")

        # Reset search path to access shared tables
        cursor.execute("SET search_path TO public")

        # Migrate each user
        migrated_count = 0
        skipped_count = 0

        for user_data in users_data:
            user_id, email, first_name, last_name, phone, is_active, is_tenant_admin, is_staff, date_joined, updated_at, last_login, profile_picture = user_data

            # Check if user already exists in shared table
            if User.objects.filter(email=email).exists():
                print(f"  [SKIP] User {email} already exists in shared table")
                skipped_count += 1
                continue

            # Create user in shared table
            try:
                # We need to get the password hash from the old table
                cursor.execute(f"SET search_path TO {schema_name}")
                cursor.execute("SELECT password FROM users WHERE id = %s", [user_id])
                password_row = cursor.fetchone()
                password = password_row[0] if password_row else ''

                cursor.execute("SET search_path TO public")

                # Insert user directly into shared table
                cursor.execute("""
                    INSERT INTO users (
                        id, email, first_name, last_name, phone,
                        password, is_active, is_tenant_admin, is_staff,
                        tenant_id, date_joined, updated_at, last_login
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    user_id, email, first_name, last_name, phone,
                    password, is_active, is_tenant_admin, is_staff,
                    org.id, date_joined, updated_at, last_login
                ])

                print(f"  [MIGRATED] {email}")
                migrated_count += 1

            except Exception as e:
                print(f"  [ERROR] Failed to migrate {email}: {e}")

        print(f"\n[SUMMARY] Schema: {schema_name}")
        print(f"  Migrated: {migrated_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total: {len(users_data)}")

def migrate_all_tenants():
    """Migrate users from all tenant schemas."""
    print("=" * 60)
    print("MIGRATE EXISTING USERS TO SHARED ACCOUNTS TABLE")
    print("=" * 60)
    print("\nWARNING: This will migrate all users from tenant schemas")
    print("to the shared accounts table. Make sure to backup first!")
    print("\nPress Ctrl+C to cancel, or")
    input("Press Enter to continue...")

    # Get all organizations
    organizations = Organization.objects.all()

    if not organizations:
        print("\n[INFO] No organizations found. Nothing to migrate.")
        return

    print(f"\n[FOUND] {organizations.count()} organization(s)")

    # Migrate users from each tenant
    for org in organizations:
        migrate_users_from_schema(org.schema_name)

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETED")
    print("=" * 60)

    # Verify migration
    total_users = User.objects.count()
    print(f"\nTotal users in shared table: {total_users}")

    # Show users per tenant
    print("\nUsers per tenant:")
    for org in organizations:
        user_count = User.objects.filter(tenant=org).count()
        print(f"  {org.slug}: {user_count} users")

    superusers = User.objects.filter(tenant__isnull=True).count()
    print(f"  Platform Superusers: {superusers}")

if __name__ == '__main__':
    migrate_all_tenants()
