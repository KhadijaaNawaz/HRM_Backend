"""
Models for notification system.

Provides real-time notification tracking for tenant events
including leave applications, approvals, and attendance events.
"""

import uuid
from django.db import models


class NotificationType(models.TextChoices):
    """Enumeration of notification types."""

    # Leave notifications
    LEAVE_APPLIED = 'leave_applied', 'Leave Applied'
    LEAVE_APPROVED = 'leave_approved', 'Leave Approved'
    LEAVE_REJECTED = 'leave_rejected', 'Leave Rejected'
    LEAVE_CANCELLED = 'leave_cancelled', 'Leave Cancelled'

    # Attendance notifications
    CHECKIN = 'checkin', 'Check-in'
    CHECKOUT = 'checkout', 'Check-out'

    # User notifications
    USER_CREATED = 'user_created', 'User Created'
    ROLE_ASSIGNED = 'role_assigned', 'Role Assigned'

    # General notifications
    MENTION = 'mention', 'Mention'
    SYSTEM = 'system', 'System'
    INFO = 'info', 'Information'


class Notification(models.Model):
    """
    Model for storing user notifications.

    Notifications are tenant-isolated and created automatically
    via signals when relevant events occur.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who receives this notification'
    )
    title = models.CharField(
        max_length=200,
        help_text='Notification title'
    )
    message = models.TextField(
        help_text='Notification message content'
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
        help_text='Type of notification'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the notification has been read'
    )
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text='URL to navigate when notification is clicked'
    )
    action_text = models.CharField(
        max_length=100,
        blank=True,
        help_text='Text for the action button'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata associated with the notification'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when notification was created'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when notification was marked as read'
    )

    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        """Return string representation of notification."""
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])
