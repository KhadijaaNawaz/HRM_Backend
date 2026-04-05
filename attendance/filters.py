"""
Filters for attendance tracking.

Provides filtering, searching, and ordering for attendance records.
"""

from django_filters import rest_framework as filters
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Attendance, AttendanceStatus


class AttendanceFilter(filters.FilterSet):
    """
    Filter for attendance records.

    Query parameters:
    - date: Exact date match (YYYY-MM-DD)
    - date_gte: Date from (inclusive)
    - date_lte: Date to (inclusive)
    - date_range: Date range (format: YYYY-MM-DD,YYYY-MM-DD)
    - status: Attendance status (present, absent, half_day, late)
    - user: User ID (UUID)
    - user_email: User email (exact match)
    - user_email_contains: User email (partial match)
    - month: Month number (1-12)
    - year: Year (YYYY)
    - has_checkin: Filter by check-in presence (true/false)
    - has_checkout: Filter by check-out presence (true/false)
    - checkin_time_after: Check-in time after (ISO datetime)
    - checkin_time_before: Check-in time before (ISO datetime)
    - today: Show only today's records (true)
    - this_week: Show only this week's records (true)
    - this_month: Show only this month's records (true)
    """

    # Date range filters
    date_gte = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_lte = filters.DateFilter(field_name='date', lookup_expr='lte')

    # Status filter
    status = filters.MultipleChoiceFilter(
        choices=AttendanceStatus.choices,
        method='filter_status'
    )

    # User filters
    user = filters.UUIDFilter(field_name='user__id')
    user_email = filters.CharFilter(field_name='user__email', lookup_expr='iexact')
    user_email_contains = filters.CharFilter(field_name='user__email', lookup_expr='icontains')

    # Month/year filters
    month = filters.NumberFilter(method='filter_month')
    year = filters.NumberFilter(method='filter_year')

    # Check-in/check-out presence filters
    has_checkin = filters.BooleanFilter(field_name='checkin_time', lookup_expr='isnull')
    has_checkout = filters.BooleanFilter(field_name='checkout_time', lookup_expr='isnull')

    # Check-in time range filters
    checkin_time_after = filters.DateTimeFilter(field_name='checkin_time', lookup_expr='gte')
    checkin_time_before = filters.DateTimeFilter(field_name='checkin_time', lookup_expr='lte')

    # Convenience filters for common date ranges
    today = filters.BooleanFilter(method='filter_today')
    this_week = filters.BooleanFilter(method='filter_this_week')
    this_month = filters.BooleanFilter(method='filter_this_month')

    # Search filter
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Attendance
        fields = ['date', 'user', 'status']

    def filter_status(self, queryset, name, value):
        """Filter by multiple status values."""
        if not value:
            return queryset
        return queryset.filter(status__in=value)

    def filter_month(self, queryset, name, value):
        """Filter by month."""
        if not value or not 1 <= value <= 12:
            return queryset
        return queryset.filter(date__month=value)

    def filter_year(self, queryset, name, value):
        """Filter by year."""
        if not value:
            return queryset
        return queryset.filter(date__year=value)

    def filter_today(self, queryset, name, value):
        """Filter for today's records only."""
        if value:
            today = timezone.now().date()
            return queryset.filter(date=today)
        return queryset

    def filter_this_week(self, queryset, name, value):
        """Filter for this week's records only."""
        if value:
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            return queryset.filter(date__gte=start_of_week, date__lte=today)
        return queryset

    def filter_this_month(self, queryset, name, value):
        """Filter for this month's records only."""
        if value:
            today = timezone.now().date()
            start_of_month = today.replace(day=1)
            return queryset.filter(date__gte=start_of_month, date__lte=today)
        return queryset

    def filter_search(self, queryset, name, value):
        """Search across multiple fields."""
        if not value:
            return queryset
        return queryset.filter(
            user__email__icontains=value
        ) | queryset.filter(
            user__first_name__icontains=value
        ) | queryset.filter(
            user__last_name__icontains=value
        ) | queryset.filter(
            notes__icontains=value
        )
