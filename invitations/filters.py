"""
Filters for invitation management.

Provides filtering, searching, and ordering for invitations.
"""

from django_filters import rest_framework as filters
from django.utils import timezone
from datetime import timedelta
from .models import Invitation, InvitationStatus, InvitationEmailLog


class InvitationFilter(filters.FilterSet):
    """
    Filter for invitation records.

    Query parameters:
    - email: Email address (exact match, case-insensitive)
    - email_contains: Email address (partial match)
    - status: Invitation status (pending, accepted, cancelled, expired)
    - status_contains: Status (partial match)
    - first_name: First name (partial match)
    - last_name: Last name (partial match)
    - invited_by: Invited by user ID (UUID)
    - invited_by_email: Invited by user email (partial match)
    - created_after: Creation date after (YYYY-MM-DD)
    - created_before: Creation date before (YYYY-MM-DD)
    - created_days: Created within X days ago
    - expires_after: Expiration date after (YYYY-MM-DD)
    - expires_before: Expiration date before (YYYY-MM-DD)
    - is_expired: Filter expired invitations (true)
    - is_valid: Filter valid invitations (true)
    - accepted_after: Accepted date after (YYYY-MM-DD)
    - accepted_before: Accepted date before (YYYY-MM-DD)
    - search: Global search across email and names
    """

    email = filters.CharFilter(field_name='email', lookup_expr='iexact')
    email_contains = filters.CharFilter(field_name='email', lookup_expr='icontains')
    status = filters.MultipleChoiceFilter(choices=InvitationStatus.choices)
    first_name = filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='last_name', lookup_expr='icontains')
    invited_by = filters.UUIDFilter(field_name='invited_by__id')
    invited_by_email = filters.CharFilter(field_name='invited_by__email', lookup_expr='icontains')
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    created_days = filters.NumberFilter(method='filter_created_days')
    expires_after = filters.DateFilter(field_name='expires_at', lookup_expr='date__gte')
    expires_before = filters.DateFilter(field_name='expires_at', lookup_expr='date__lte')
    accepted_after = filters.DateFilter(field_name='accepted_at', lookup_expr='date__gte')
    accepted_before = filters.DateFilter(field_name='accepted_at', lookup_expr='date__lte')
    is_expired = filters.BooleanFilter(method='filter_is_expired')
    is_valid = filters.BooleanFilter(method='filter_is_valid')
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Invitation
        fields = ['email', 'status', 'invited_by', 'created_at', 'expires_at', 'accepted_at']

    def filter_created_days(self, queryset, name, value):
        """Filter invitations created within X days ago."""
        if not value or value <= 0:
            return queryset
        cutoff_date = timezone.now() - timedelta(days=value)
        return queryset.filter(created_at__date__gte=cutoff_date)

    def filter_is_expired(self, queryset, name, value):
        """Filter expired invitations."""
        if value is True:
            return queryset.filter(expires_at__lt=timezone.now())
        return queryset.filter(expires_at__gte=timezone.now())

    def filter_is_valid(self, queryset, name, value):
        """Filter valid (pending and not expired) invitations."""
        if value is True:
            return queryset.filter(
                status=InvitationStatus.PENDING,
                expires_at__gte=timezone.now()
            )
        return queryset

    def filter_search(self, queryset, name, value):
        """Global search across email and names."""
        if not value:
            return queryset
        return queryset.filter(
            email__icontains=value
        ) | queryset.filter(
            first_name__icontains=value
        ) | queryset.filter(
            last_name__icontains=value
        )


class InvitationEmailLogFilter(filters.FilterSet):
    """
    Filter for invitation email logs.

    Query parameters:
    - invitation: Invitation ID (UUID)
    - invitation_email: Invitation email (partial match)
    - sent_after: Sent date after (YYYY-MM-DD)
    - sent_before: Sent date before (YYYY-MM-DD)
    - status: Email status (sent, failed, bounced)
    - status_contains: Status (partial match)
    """

    invitation = filters.UUIDFilter(field_name='invitation__id')
    invitation_email = filters.CharFilter(field_name='invitation__email', lookup_expr='icontains')
    sent_after = filters.DateFilter(field_name='sent_at', lookup_expr='date__gte')
    sent_before = filters.DateFilter(field_name='sent_at', lookup_expr='date__lte')
    status = filters.CharFilter(field_name='status', lookup_expr='iexact')
    status_contains = filters.CharFilter(field_name='status', lookup_expr='icontains')

    class Meta:
        model = InvitationEmailLog
        fields = ['invitation', 'sent_at', 'status']
