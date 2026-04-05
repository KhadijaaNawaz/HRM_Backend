"""
Attendance tracking models for HRM SaaS.

This module defines the Attendance model for tracking employee
check-in/check-out times with location support.
"""

import uuid
from datetime import date, datetime
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class AttendanceStatus(models.TextChoices):
    """Attendance status choices."""
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    HALF_DAY = 'half_day', 'Half Day'
    LATE = 'late', 'Late'


class Attendance(models.Model):
    """
    Attendance record for tracking employee check-in/check-out.

    Each record represents a single day's attendance for a user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date = models.DateField()

    # Check-in/out times
    checkin_time = models.DateTimeField(null=True, blank=True)
    checkout_time = models.DateTimeField(null=True, blank=True)

    # Additional information
    notes = models.TextField(blank=True)
    location = models.JSONField(null=True, blank=True)  # {lat, lng}
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        ordering = ['-date', '-checkin_time']
        unique_together = ['user', 'date']  # One attendance record per user per day

    def __str__(self):
        return f"{self.user.email} - {self.date}"

    @property
    def hours_worked(self):
        """Calculate hours worked between check-in and check-out."""
        if self.checkin_time and self.checkout_time:
            delta = self.checkout_time - self.checkin_time
            return round(delta.total_seconds() / 3600, 2)
        return None

    def clean(self):
        """Validate attendance record."""
        # Check that checkout is after checkin
        if self.checkin_time and self.checkout_time:
            if self.checkout_time <= self.checkin_time:
                raise ValidationError(
                    'Checkout time must be after check-in time.'
                )

        # Check that date matches checkin_time date
        if self.checkin_time:
            checkin_date = self.checkin_time.date()
            if checkin_date != self.date:
                raise ValidationError(
                    f'Check-in date ({checkin_date}) must match attendance date ({self.date}).'
                )

    def save(self, *args, **kwargs):
        """Override save to validate and calculate status."""
        self.full_clean()
        super().save(*args, **kwargs)


class AttendanceSettings(models.Model):
    """
    Attendance settings per organization.

    Stores organization-wide attendance settings like
    working hours, grace periods, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Working hours
    work_start_time = models.TimeField(default='09:00')
    work_end_time = models.TimeField(default='17:00')
    grace_period_minutes = models.IntegerField(default=15)

    # Break settings
    break_duration_minutes = models.IntegerField(default=60)

    # Overtime settings
    overtime_enabled = models.BooleanField(default=True)
    overtime_start_after_minutes = models.IntegerField(default=8 * 60)  # After 8 hours

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_settings'
        verbose_name = 'Attendance Settings'
        verbose_name_plural = 'Attendance Settings'

    def __str__(self):
        return f"Attendance Settings"
