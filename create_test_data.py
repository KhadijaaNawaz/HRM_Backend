"""
Create test data for HRM SaaS platform.
Run with: python manage.py shell < create_test_data.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from tenants.models import Organization, Domain
from django_tenants.utils import schema_context, tenant_context
from django.db import connection

def create_test_organization():
    """Create a test organization/tenant."""
    print("=" * 60)
    print("CREATING TEST ORGANIZATION")
    print("=" * 60)

    # Check if organization exists
    org = Organization.objects.filter(slug='acme').first()

    if org:
        print(f"[OK] Organization exists: {org.name}")
        print(f"     Slug: {org.slug}")
        print(f"     Schema: {org.schema_name}")
        print(f"     Status: {org.status}")
    else:
        # Create organization
        org = Organization.objects.create(
            name='Acme Corporation',
            slug='acme',
            status='active'
        )

        # Create domain
        domain = Domain.objects.create(
            domain='acme.localhost',
            tenant=org,
            is_primary=True
        )

        print(f"[CREATED] Organization: {org.name}")
        print(f"          Slug: {org.slug}")
        print(f"          Schema: {org.schema_name}")
        print(f"          Domain: {domain.domain}")

    print()
    return org


def create_test_roles(org):
    """Create default roles for the organization."""
    print("=" * 60)
    print("CREATING TEST ROLES")
    print("=" * 60)

    with tenant_context(org):
        from accounts.models import Role

        roles_data = [
            {'name': 'Admin', 'description': 'Full system administrator', 'is_system_role': True},
            {'name': 'HR', 'description': 'Human Resources Manager', 'is_system_role': True},
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
            else:
                print(f"[OK] Role exists: {role.name}")

    print()


def create_test_users(org):
    """Create test users for the organization."""
    print("=" * 60)
    print("CREATING TEST USERS")
    print("=" * 60)

    with tenant_context(org):
        from accounts.models import User, Role, UserRole

        # Test users data
        users_data = [
            {
                'email': 'admin@acme.com',
                'password': 'Admin123!',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_tenant_admin': True,
                'roles': ['Admin']
            },
            {
                'email': 'hr@acme.com',
                'password': 'HrManager123!',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'is_tenant_admin': False,
                'roles': ['HR', 'HR Manager']
            },
            {
                'email': 'john.doe@acme.com',
                'password': 'Employee123!',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_tenant_admin': False,
                'roles': ['Employee']
            },
            {
                'email': 'jane.smith@acme.com',
                'password': 'Employee123!',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'is_tenant_admin': False,
                'roles': ['Employee']
            },
        ]

        for user_data in users_data:
            email = user_data['email']
            roles = user_data.pop('roles')

            # Check if user exists
            user = User.objects.filter(email=email).first()

            if user:
                print(f"[OK] User exists: {email}")

                # Update roles
                for role_name in roles:
                    role = Role.objects.filter(name=role_name).first()
                    if role:
                        UserRole.objects.get_or_create(user=user, role=role)
            else:
                # Create user
                user = User.objects.create_user(**user_data)
                print(f"[CREATED] User: {email}")

                # Assign roles
                for role_name in roles:
                    role = Role.objects.filter(name=role_name).first()
                    if role:
                        UserRole.objects.create(user=user, role=role)
                        print(f"          -> Assigned role: {role_name}")

    print()


def create_test_attendance(org):
    """Create sample attendance records."""
    print("=" * 60)
    print("CREATING SAMPLE ATTENDANCE")
    print("=" * 60)

    from datetime import date, timedelta, datetime
    from django.utils import timezone

    with tenant_context(org):
        from accounts.models import User
        from attendance.models import Attendance, AttendanceStatus

        # Get employees - use UserRole to filter by role
        employee_ids = User.objects.filter(
            user_roles__role__name='Employee'
        ).values_list('id', flat=True).distinct()

        employees = User.objects.filter(id__in=employee_ids, is_active=True)

        today = date.today()

        for employee in employees:
            # Create attendance for last 5 days
            for days_ago in range(5, 0, -1):
                attendance_date = today - timedelta(days=days_ago)

                # Check if attendance exists
                existing = Attendance.objects.filter(
                    user=employee,
                    date=attendance_date
                ).first()

                if existing:
                    continue

                # Create check-in time
                checkin_time = datetime.combine(
                    attendance_date,
                    datetime.min.time()
                ).replace(hour=9, minute=0 + (days_ago * 5))

                # Create checkout time
                checkout_time = datetime.combine(
                    attendance_date,
                    datetime.min.time()
                ).replace(hour=17, minute=0)

                # Skip weekends
                if attendance_date.weekday() >= 5:
                    continue

                attendance = Attendance.objects.create(
                    user=employee,
                    date=attendance_date,
                    checkin_time=checkin_time,
                    checkout_time=checkout_time,
                    status=AttendanceStatus.PRESENT
                )
                print(f"[CREATED] Attendance: {employee.email} - {attendance_date}")

    print()


def print_summary(org):
    """Print summary of created data."""
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    with tenant_context(org):
        from accounts.models import User, Role
        from attendance.models import Attendance

        users_count = User.objects.filter(is_active=True).count()
        roles_count = Role.objects.count()
        attendance_count = Attendance.objects.count()

        print(f"Organization: {org.name} ({org.slug})")
        print(f"Total Users: {users_count}")
        print(f"Total Roles: {roles_count}")
        print(f"Attendance Records: {attendance_count}")
        print()
        print("=" * 60)
        print("TEST CREDENTIALS")
        print("=" * 60)
        print()
        print("Tenant ID: acme")
        print()
        print("ADMIN USER:")
        print("  Email: admin@acme.com")
        print("  Password: Admin123!")
        print()
        print("HR USER:")
        print("  Email: hr@acme.com")
        print("  Password: HrManager123!")
        print()
        print("EMPLOYEE USERS:")
        print("  Email: john.doe@acme.com")
        print("  Password: Employee123!")
        print("  Email: jane.smith@acme.com")
        print("  Password: Employee123!")
        print()
        print("=" * 60)
        print("READY TO TEST!")
        print("=" * 60)


def main():
    """Main function to create all test data."""
    try:
        # Create organization
        org = create_test_organization()

        # Create roles
        create_test_roles(org)

        # Create users
        create_test_users(org)

        # Create sample attendance
        create_test_attendance(org)

        # Print summary
        print_summary(org)

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
