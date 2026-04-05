"""
Leave management models for HRM SaaS.

This module defines the Leave and LeaveBalance models for tracking employee leave requests,
balances, and approval workflows.
"""

import uuid
from datetime import date, datetime, timedelta
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class LeaveType(models.TextChoices):
    """Leave type choices."""
    CASUAL = 'casual', 'Casual Leave'
    SICK = 'sick', 'Sick Leave'
    EARNED = 'earned', 'Earned/Vacation Leave'
    UNPAID = 'unpaid', 'Unpaid Leave'
    MATERNITY = 'maternity', 'Maternity Leave'
    PATERNITY = 'paternity', 'Paternity Leave'
    COMP_OFF = 'comp_off', 'Compensatory Off'


class LeaveStatus(models.TextChoices):
    """Leave status choices."""
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'
    CANCELLED = 'cancelled', 'Cancelled'


class Leave(models.Model):
    """
    Leave application model for tracking employee leave requests.

    Each leave request spans a date range and requires approval from HR/Admin.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Employee and leave details
    employee = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LeaveType.choices
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)

    # Approval workflow
    status = models.CharField(
        max_length=20,
        choices=LeaveStatus.choices,
        default=LeaveStatus.PENDING
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_leaves'
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leaves'
        verbose_name = 'Leave'
        verbose_name_plural = 'Leaves'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"

    @property
    def days(self):
        """Calculate the number of leave days."""
        return (self.end_date - self.start_date).days + 1

    @property
    def is_pending(self):
        """Check if leave is pending approval."""
        return self.status == LeaveStatus.PENDING

    @property
    def is_approved(self):
        """Check if leave is approved."""
        return self.status == LeaveStatus.APPROVED

    @property
    def is_rejected(self):
        """Check if leave is rejected."""
        return self.status == LeaveStatus.REJECTED

    @property
    def is_cancelled(self):
        """Check if leave is cancelled."""
        return self.status == LeaveStatus.CANCELLED

    def clean(self):
        """Validate leave request."""
        # Validate date range
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError({
                    'start_date': 'Start date must be before or equal to end date.',
                    'end_date': 'End date must be after or equal to start date.'
                })

            # Check for overlapping leaves
            overlapping = Leave.objects.filter(
                employee=self.employee,
                status__in=[LeaveStatus.PENDING, LeaveStatus.APPROVED],
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )

            # Exclude current instance if updating
            if self.id:
                overlapping = overlapping.exclude(id=self.id)

            if overlapping.exists():
                raise ValidationError({
                    'start_date': 'You have overlapping leave requests for this period.',
                    'end_date': 'You have overlapping leave requests for this period.'
                })

        # Validate dates are in future (unless admin)
        if self.start_date and self.start_date < date.today():
            raise ValidationError({
                'start_date': 'Leave start date must be today or in the future.'
            })

    def save(self, *args, **kwargs):
        """Override save to validate and update timestamps."""
        self.full_clean()
        super().save(*args, **kwargs)

    def approve(self, approver, comment=''):
        """Approve the leave request."""
        self.status = LeaveStatus.APPROVED
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.save()

    def reject(self, rejecter, reason=''):
        """Reject the leave request."""
        self.status = LeaveStatus.REJECTED
        self.rejected_by = rejecter
        self.rejected_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    def cancel(self):
        """Cancel the leave request."""
        if self.status not in [LeaveStatus.PENDING, LeaveStatus.APPROVED]:
            raise ValueError("Only pending or approved leaves can be cancelled.")
        self.status = LeaveStatus.CANCELLED
        self.save()


class LeaveBalance(models.Model):
    """
    Leave balance model for tracking employee leave balances per year.

    Maintains the balance for each type of leave for each employee per year.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='leave_balances'
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LeaveType.choices
    )
    year = models.IntegerField()

    # Balance tracking
    total_days = models.IntegerField(default=0, help_text='Total allocated days')
    used_days = models.IntegerField(default=0, help_text='Days used this year')
    balance_days = models.IntegerField(default=0, help_text='Remaining balance days')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_balances'
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        ordering = ['employee', 'leave_type', 'year']
        unique_together = ['employee', 'leave_type', 'year']
        indexes = [
            models.Index(fields=['employee', 'year']),
            models.Index(fields=['leave_type', 'year']),
        ]

    def __str__(self):
        return f"{self.employee.email} - {self.get_leave_type_display()} ({self.year}): {self.balance_days} days"

    @classmethod
    def get_balance(cls, employee, leave_type, year=None):
        """Get leave balance for an employee."""
        if not year:
            year = date.today().year

        balance, created = cls.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=year,
            defaults={
                'total_days': 0,
                'used_days': 0,
                'balance_days': 0
            }
        )

        # Recalculate balance
        balance.recalculate_balance()
        return balance

    def recalculate_balance(self):
        """Recalculate balance based on used leaves."""
        self.used_days = self.employee.leaves.filter(
            leave_type=self.leave_type,
            status=LeaveStatus.APPROVED,
            start_date__year=self.year
        ).aggregate(
            total_used=models.Sum('days')
        )['total_used'] or 0

        self.balance_days = max(0, self.total_days - self.used_days)
        self.save()
