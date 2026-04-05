"""
Admin configuration for leave models.
"""

from django.contrib import admin
from .models import Leave, LeaveBalance


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    """Admin interface for Leave model."""
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status', 'days', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date', 'created_at']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    """Admin interface for LeaveBalance model."""
    list_display = ['employee', 'leave_type', 'year', 'total_days', 'used_days', 'balance_days']
    list_filter = ['leave_type', 'year']
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['created_at', 'updated_at']
