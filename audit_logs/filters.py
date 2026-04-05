"""
Filters for audit log management.

Provides filtering, searching, and ordering for audit logs.
"""

from django_filters import rest_framework as filters
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog


class AuditLogFilter(filters.FilterSet):
    """
    Filter for audit log records.

    Query parameters:
    - action: Action type (exact match)
    - action_contains: Action type (partial match)
    - user: User ID (UUID)
    - user_email: User email (partial match)
    - target_model: Target model (exact match)
    - target_id: Target object ID (partial match)
    - timestamp_after: Timestamp after (ISO datetime)
    - timestamp_before: Timestamp before (ISO datetime)
    - timestamp_date: Timestamp date (YYYY-MM-DD)
    - timestamp_days: Timestamp within X days ago
    - ip_address: IP address (partial match)
    - meta_key: Filter by meta JSON key (e.g., meta_key=created_email)
    - search: Global search across action, target_model, target_id
    """

    action = filters.CharFilter(field_name='action', lookup_expr='iexact')
    action_contains = filters.CharFilter(field_name='action', lookup_expr='icontains')
    user = filters.UUIDFilter(field_name='user__id')
    user_email = filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    target_model = filters.CharFilter(field_name='target_model', lookup_expr='iexact')
    target_model_contains = filters.CharFilter(field_name='target_model', lookup_expr='icontains')
    target_id = filters.CharFilter(field_name='target_id', lookup_expr='icontains')
    timestamp_after = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_before = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    timestamp_date = filters.DateFilter(field_name='timestamp', lookup_expr='date')
    timestamp_days = filters.NumberFilter(method='filter_timestamp_days')
    ip_address = filters.CharFilter(field_name='ip_address', lookup_expr='icontains')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = AuditLog
        fields = ['action', 'user', 'target_model', 'target_id', 'timestamp', 'ip_address']

    def filter_timestamp_days(self, queryset, name, value):
        """Filter logs within X days ago."""
        if not value or value <= 0:
            return queryset
        cutoff_date = timezone.now() - timedelta(days=value)
        return queryset.filter(timestamp__gte=cutoff_date)

    def filter_search(self, queryset, name, value):
        """Global search across multiple fields."""
        if not value:
            return queryset
        return queryset.filter(
            action__icontains=value
        ) | queryset.filter(
            target_model__icontains=value
        ) | queryset.filter(
            target_id__icontains=value
        ) | queryset.filter(
            user__email__icontains=value
        )
