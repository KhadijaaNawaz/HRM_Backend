"""
Filters for user and role management.

Provides filtering, searching, and ordering for users and roles.
"""

from django_filters import rest_framework as filters
from django.utils import timezone
from datetime import timedelta
from .models import User, Role, UserRole


class UserFilter(filters.FilterSet):
    """
    Filter for user records.

    Query parameters:
    - email: Email address (exact match, case-insensitive)
    - email_contains: Email address (partial match)
    - first_name: First name (exact match, case-insensitive)
    - first_name_contains: First name (partial match)
    - last_name: Last name (exact match, case-insensitive)
    - last_name_contains: Last name (partial match)
    - name: Full name search (searches both first and last name)
    - phone: Phone number (partial match)
    - is_active: Active status (true/false)
    - is_tenant_admin: Tenant admin status (true/false)
    - is_staff: Django staff status (true/false)
    - role: Role name (exact match)
    - role_contains: Role name (partial match)
    - joined_after: Join date after (YYYY-MM-DD)
    - joined_before: Join date before (YYYY-MM-DD)
    - last_login_after: Last login after (YYYY-MM-DD)
    - last_login_before: Last login before (YYYY-MM-DD)
    - last_login_days: Last login within X days ago
    - never_logged_in: Users who never logged in (true)
    - search: Global search across email, first_name, last_name
    """

    # Email filters
    email = filters.CharFilter(field_name='email', lookup_expr='iexact')
    email_contains = filters.CharFilter(field_name='email', lookup_expr='icontains')

    # Name filters
    first_name = filters.CharFilter(field_name='first_name', lookup_expr='iexact')
    first_name_contains = filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='last_name', lookup_expr='iexact')
    last_name_contains = filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    name = filters.CharFilter(method='filter_name')

    # Phone filter
    phone = filters.CharFilter(field_name='phone', lookup_expr='icontains')

    # Boolean filters
    is_active = filters.BooleanFilter()
    is_tenant_admin = filters.BooleanFilter()
    is_staff = filters.BooleanFilter()

    # Role filters
    role = filters.CharFilter(method='filter_role')
    role_contains = filters.CharFilter(method='filter_role_contains')

    # Date range filters for date_joined
    joined_after = filters.DateFilter(field_name='date_joined', lookup_expr='date__gte')
    joined_before = filters.DateFilter(field_name='date_joined', lookup_expr='date__lte')
    joined_date = filters.DateFilter(field_name='date_joined', lookup_expr='date')

    # Date range filters for last_login
    last_login_after = filters.DateTimeFilter(field_name='last_login', lookup_expr='gte')
    last_login_before = filters.DateTimeFilter(field_name='last_login', lookup_expr='lte')
    last_login_days = filters.NumberFilter(method='filter_last_login_days')
    never_logged_in = filters.BooleanFilter(field_name='last_login', lookup_expr='isnull')

    # Search filter
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active', 'is_tenant_admin', 'is_staff']

    def filter_name(self, queryset, name, value):
        """Filter by full name (searches both first and last name)."""
        if not value:
            return queryset
        return queryset.filter(
            first_name__icontains=value
        ) | queryset.filter(
            last_name__icontains=value
        )

    def filter_role(self, queryset, name, value):
        """Filter by exact role name."""
        if not value:
            return queryset
        return queryset.filter(roles__name=value).distinct()

    def filter_role_contains(self, queryset, name, value):
        """Filter by partial role name."""
        if not value:
            return queryset
        return queryset.filter(roles__name__icontains=value).distinct()

    def filter_last_login_days(self, queryset, name, value):
        """Filter users who logged in within X days ago."""
        if not value or value <= 0:
            return queryset
        cutoff_date = timezone.now() - timedelta(days=value)
        return queryset.filter(last_login__gte=cutoff_date)

    def filter_search(self, queryset, name, value):
        """Global search across multiple fields."""
        if not value:
            return queryset
        return queryset.filter(
            email__icontains=value
        ) | queryset.filter(
            first_name__icontains=value
        ) | queryset.filter(
            last_name__icontains=value
        ) | queryset.filter(
            phone__icontains=value
        )


class RoleFilter(filters.FilterSet):
    """
    Filter for role records.

    Query parameters:
    - name: Role name (exact match, case-insensitive)
    - name_contains: Role name (partial match)
    - is_system_role: System role flag (true/false)
    - description: Description (partial match)
    - search: Global search across name and description
    """

    name = filters.CharFilter(field_name='name', lookup_expr='iexact')
    name_contains = filters.CharFilter(field_name='name', lookup_expr='icontains')
    is_system_role = filters.BooleanFilter()
    description = filters.CharFilter(field_name='description', lookup_expr='icontains')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Role
        fields = ['name', 'is_system_role']

    def filter_search(self, queryset, name, value):
        """Global search across name and description."""
        if not value:
            return queryset
        return queryset.filter(
            name__icontains=value
        ) | queryset.filter(
            description__icontains=value
        )


class UserRoleFilter(filters.FilterSet):
    """
    Filter for user-role assignments.

    Query parameters:
    - user: User ID (UUID)
    - user_email: User email (partial match)
    - role: Role ID (UUID)
    - role_name: Role name (partial match)
    - assigned_after: Assignment date after (YYYY-MM-DD)
    - assigned_before: Assignment date before (YYYY-MM-DD)
    - assigned_by: Assigned by user ID (UUID)
    """

    user = filters.UUIDFilter(field_name='user__id')
    user_email = filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    role = filters.UUIDFilter(field_name='role__id')
    role_name = filters.CharFilter(field_name='role__name', lookup_expr='icontains')
    assigned_after = filters.DateFilter(field_name='assigned_at', lookup_expr='date__gte')
    assigned_before = filters.DateFilter(field_name='assigned_at', lookup_expr='date__lte')
    assigned_by = filters.UUIDFilter(field_name='assigned_by__id')

    class Meta:
        model = UserRole
        fields = ['user', 'role', 'assigned_by', 'assigned_at']
