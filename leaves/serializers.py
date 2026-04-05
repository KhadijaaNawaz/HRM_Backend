"""
Serializers for leave management.

Provides serializers for leave CRUD operations, approval workflows,
and leave balance management.
"""

from rest_framework import serializers
from django.utils import timezone
from django.db.models import Sum, Q, F
from .models import Leave, LeaveBalance, LeaveType, LeaveStatus


class LeaveSerializer(serializers.ModelSerializer):
    """Basic serializer for Leave model."""
    days = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()
    is_approved = serializers.ReadOnlyField()
    is_rejected = serializers.ReadOnlyField()
    is_cancelled = serializers.ReadOnlyField()

    class Meta:
        model = Leave
        fields = [
            'id', 'employee', 'leave_type', 'start_date', 'end_date',
            'reason', 'status', 'approved_by', 'approved_at',
            'rejected_by', 'rejected_at', 'rejection_reason',
            'created_at', 'updated_at', 'days', 'is_pending',
            'is_approved', 'is_rejected', 'is_cancelled'
        ]
        read_only_fields = [
            'id', 'status', 'approved_by', 'approved_at',
            'rejected_by', 'rejected_at', 'rejection_reason',
            'created_at', 'updated_at'
        ]


class LeaveDetailSerializer(LeaveSerializer):
    """Detailed serializer for Leave with nested employee information."""
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    approver_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    rejecter_name = serializers.CharField(source='rejected_by.get_full_name', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(LeaveSerializer.Meta):
        fields = LeaveSerializer.Meta.fields + [
            'employee_email', 'employee_name', 'approver_name',
            'rejecter_name', 'leave_type_display', 'status_display'
        ]


class CreateLeaveSerializer(serializers.ModelSerializer):
    """Serializer for creating a new leave request."""

    class Meta:
        model = Leave
        fields = [
            'leave_type', 'start_date', 'end_date', 'reason'
        ]

    def validate_start_date(self, value):
        """Validate that start date is not in the past."""
        if value < timezone.now().date():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate_end_date(self, value):
        """Validate that end date is not before start date."""
        # This will be cross-validated with start_date in validate()
        return value

    def validate(self, attrs):
        """Cross-validate date range and check for overlapping leaves."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after or equal to start date.'
                })

        return attrs


class ApproveLeaveSerializer(serializers.Serializer):
    """Serializer for approving a leave request."""
    comment = serializers.CharField(required=False, allow_blank=True)


class RejectLeaveSerializer(serializers.Serializer):
    """Serializer for rejecting a leave request."""
    reason = serializers.CharField(required=True, help_text="Reason for rejection")


class CancelLeaveSerializer(serializers.Serializer):
    """Serializer for cancelling a leave request."""
    pass


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for LeaveBalance model."""

    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'employee', 'leave_type', 'year',
            'total_days', 'used_days', 'balance_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)


class MyLeaveSerializer(LeaveDetailSerializer):
    """Serializer for employee's own leave requests."""
    pass


class LeaveSummarySerializer(serializers.Serializer):
    """Serializer for leave summary statistics."""
    total_leaves = serializers.IntegerField()
    pending_leaves = serializers.IntegerField()
    approved_leaves = serializers.IntegerField()
    rejected_leaves = serializers.IntegerField()
    cancelled_leaves = serializers.IntegerField()

    # Breakdown by leave type
    by_type = serializers.DictField()

    # This month's stats
    this_month_pending = serializers.IntegerField()
    this_month_approved = serializers.IntegerField()
    this_month_rejected = serializers.IntegerField()

    # Upcoming leaves (approved in future)
    upcoming_leaves = serializers.IntegerField()


class LeaveBalanceSummarySerializer(serializers.Serializer):
    """Serializer for employee's leave balance summary."""
    year = serializers.IntegerField()
    balances = serializers.ListField()

    each_balance = LeaveBalanceSerializer(many=False)
