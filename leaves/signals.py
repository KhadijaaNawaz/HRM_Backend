"""
Signal handlers for leave management.

Handles signals related to leave status changes and creates
notifications when leaves are created, approved, rejected, or cancelled.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Leave


@receiver(post_save, sender=Leave)
def notify_on_leave_applied(sender, instance, created, **kwargs):
    """
    Send notification when leave is applied.

    This signal handler is triggered when a new Leave record is created.
    The actual notification creation is handled by the notifications app's
    signals to avoid circular imports.
    """
    # The notification is handled by notifications app's signals
    # to avoid circular dependencies
    pass


@receiver(post_save, sender=Leave)
def notify_on_leave_status_change(sender, instance, **kwargs):
    """
    Send notification when leave status changes.

    This signal handler is triggered when a Leave's status changes.
    The actual notification creation is handled by the notifications app's
    signals to avoid circular imports.
    """
    # The notification is handled by notifications app's signals
    # to avoid circular dependencies
    pass
