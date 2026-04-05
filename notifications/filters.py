"""
Filters for notification system.

Provides filtering, searching, and ordering for notification records.
"""

from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Notification, NotificationType


class NotificationFilter(filters.FilterSet):
    """
    Filter for notification records.

    Query parameters:
    - is_read: Filter by read status (true/false)
    - notification_type: Filter by notification type
    - created_after: Created after date (YYYY-MM-DD)
    - created_before: Created before date (YYYY-MM-DD)
    - search: Search in title and message
    """

    is_read = filters.BooleanFilter(field_name='is_read')
    notification_type = filters.MultipleChoiceFilter(choices=NotificationType.choices)

    # Date filters
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    # Search filter
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Notification
        fields = ['is_read', 'notification_type', 'created_at']

    def filter_search(self, queryset, name, value):
        """Search across title and message."""
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value) |
            Q(message__icontains=value)
        )
