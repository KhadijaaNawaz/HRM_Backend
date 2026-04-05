"""
Filters for leave management.

Provides filtering, searching, and ordering for leave records.
"""

from django_filters import rest_framework as filters
from django.db.models import Q
from .models import Leave, LeaveBalance, LeaveType, LeaveStatus


class LeaveFilter(filters.FilterSet):
    """
    Filter for leave records.

    Query parameters:
    - status: Leave status (pending, approved, rejected, cancelled)
    - employee: Employee ID (UUID)
    - employee_email: Employee email (exact match)
    - employee_email_contains: Employee email (partial match)
    - leave_type: Leave type (casual, sick, earned, etc.)
    - start_date_gte: Start date from (YYYY-MM-DD)
    - start_date_lte: Start date to (YYYY-MM-DD)
    - end_date_gte: End date from (YYYY-MM-DD)
    - end_date_lte: End date to (YYYY-MM-DD)
    - date_in_range: Filter leaves that overlap with date range
    - approved_by: Approver user ID (UUID)
    - created_after: Created after date (YYYY-MM-DD)
    - created_before: Created before date (YYYY-MM-DD)
    - search: Search in reason, employee name, employee email
    - month: Month number (1-12)
    - year: Year (YYYY)
    """

    status = filters.MultipleChoiceFilter(choices=LeaveStatus.choices)
    employee = filters.UUIDFilter(field_name='employee__id')
    employee_email = filters.CharFilter(field_name='employee__email', lookup_expr='iexact')
    employee_email_contains = filters.CharFilter(field_name='employee__email', lookup_expr='icontains')
    leave_type = filters.MultipleChoiceFilter(choices=LeaveType.choices)

    # Date range filters
    start_date_gte = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_lte = filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date_gte = filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date_lte = filters.DateFilter(field_name='end_date', lookup_expr='lte')

    # Date overlap filter (custom)
    date_in_range_start = filters.DateFilter(method='filter_date_range')
    date_in_range_end = filters.DateFilter(method='filter_date_range')

    # Approver filters
    approved_by = filters.UUIDFilter(field_name='approved_by__id')

    # Date created filters
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    # Month/year filters
    month = filters.NumberFilter(field_name='start_date__month', lookup_expr='exact')
    year = filters.NumberFilter(field_name='start_date__year', lookup_expr='exact')

    # Search filter
    search = filters.CharFilter(method='filter_search')

    class Meta:
        model = Leave
        fields = [
            'status', 'employee', 'leave_type', 'start_date', 'end_date',
            'approved_by', 'created_at'
        ]

    def filter_date_range(self, queryset, name, value):
        """Filter leaves that overlap with the given date range."""
        # This will be used with date_in_range_start and date_in_range_end
        # Store the filter value for later use
        if hasattr(self, '_date_range_start'):
            # Return leaves that overlap with [date_range_start, date_range_end]
            return queryset.filter(
                Q(start_date__lte=self._date_range_end) & Q(end_date__gte=self._date_range_start)
            )
        return queryset

    def filter_search(self, queryset, name, value):
        """Search across reason, employee name, and employee email."""
        if not value:
            return queryset
        return queryset.filter(
            Q(reason__icontains=value) |
            Q(employee__first_name__icontains=value) |
            Q(employee__last_name__icontains=value) |
            Q(employee__email__icontains=value)
        )


class LeaveBalanceFilter(filters.FilterSet):
    """
    Filter for leave balance records.

    Query parameters:
    - employee: Employee ID (UUID)
    - employee_email: Employee email (exact match)
    - leave_type: Leave type filter
    - year: Year for balance
    - has_balance: Filter by having positive balance
    """

    employee = filters.UUIDFilter(field_name='employee__id')
    employee_email = filters.CharFilter(field_name='employee__email', lookup_expr='iexact')
    leave_type = filters.MultipleChoiceFilter(choices=LeaveType.choices)
    year = filters.NumberFilter()
    has_balance = filters.BooleanFilter(method='filter_has_balance')

    class Meta:
        model = LeaveBalance
        fields = ['employee', 'leave_type', 'year']

    def filter_has_balance(self, queryset, name, value):
        """Filter by positive balance."""
        if value is True:
            return queryset.filter(balance_days__gt=0)
        return queryset
