"""
Filters for tenant/organization management.

Provides filtering, searching, and ordering for organizations.
"""

from django_filters import rest_framework as filters
from django.utils import timezone
from datetime import timedelta
from .models import Organization, OrganizationStatus


class OrganizationFilter(filters.FilterSet):
    """
    Filter for organization/tenant records.

    Query parameters:
    - name: Organization name (exact match, case-insensitive)
    - name_contains: Organization name (partial match)
    - slug: Organization slug (exact match, case-insensitive)
    - slug_contains: Organization slug (partial match)
    - status: Organization status (active, suspended, pending)
    - status_contains: Status (partial match)
    - timezone: Timezone (exact match)
    - timezone_contains: Timezone (partial match)
    - created_after: Creation date after (YYYY-MM-DD)
    - created_before: Creation date before (YYYY-MM-DD)
    - created_days: Created within X days ago
    - public_signup_enabled: Public signup flag (true/false)
    - has_domain: Filter by domain presence
    - search: Global search across name and slug
    """

    name = filters.CharFilter(field_name='name', lookup_expr='iexact')
    name_contains = filters.CharFilter(field_name='name', lookup_expr='icontains')
    slug = filters.CharFilter(field_name='slug', lookup_expr='iexact')
    slug_contains = filters.CharFilter(field_name='slug', lookup_expr='icontains')
    status = filters.MultipleChoiceFilter(choices=OrganizationStatus.choices)
    timezone = filters.CharFilter(field_name='timezone', lookup_expr='iexact')
    timezone_contains = filters.CharFilter(field_name='timezone', lookup_expr='icontains')
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    created_days = filters.NumberFilter(method='filter_created_days')
    public_signup_enabled = filters.BooleanFilter()
    has_domain = filters.BooleanFilter(field_name='domain', lookup_expr='isnull')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Organization
        fields = ['name', 'slug', 'status', 'timezone', 'public_signup_enabled']

    def filter_created_days(self, queryset, name, value):
        """Filter organizations created within X days ago."""
        if not value or value <= 0:
            return queryset
        cutoff_date = timezone.now() - timedelta(days=value)
        return queryset.filter(created_at__date__gte=cutoff_date)

    def filter_search(self, queryset, name, value):
        """Global search across name and slug."""
        if not value:
            return queryset
        return queryset.filter(
            name__icontains=value
        ) | queryset.filter(
            slug__icontains=value
        )
