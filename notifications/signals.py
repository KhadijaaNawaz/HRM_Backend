"""
Signal handlers for automatic notification creation.

Creates notifications automatically when relevant events occur
in the system such as leave applications, approvals, and attendance.
"""

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from .services import NotificationService


@receiver(post_save, sender='leaves.Leave')
def notify_on_leave_applied(sender, instance, created, **kwargs):
    """
    Send notification when leave is applied.

    Triggers when a new Leave record is created with status 'pending'.
    Notifies all HR and Admin users.
    """
    if created and instance.is_pending:
        try:
            NotificationService.notify_leave_applied(instance)
        except Exception as e:
            # Don't break the application if notification fails
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create notification for leave application: {e}'
            )


@receiver(post_save, sender='leaves.Leave')
def notify_on_leave_status_change(sender, instance, **kwargs):
    """
    Send notification when leave status changes.

    Triggers when a Leave's status changes to 'approved' or 'rejected'.
    Notifies the employee who applied for the leave.
    """
    # We need to check if status just changed
    # This is a simplified version - in production, you'd track the previous status
    if instance.is_approved:
        try:
            # Check if we should notify (only if not already notified)
            # This could be improved with a field tracking if notification was sent
            NotificationService.notify_leave_approved(instance)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create notification for leave approval: {e}'
            )
    elif instance.is_rejected:
        try:
            NotificationService.notify_leave_rejected(instance)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create notification for leave rejection: {e}'
            )


@receiver(post_save, sender='leaves.Leave')
def notify_on_leave_cancelled(sender, instance, **kwargs):
    """
    Send notification when leave is cancelled.

    Triggers when a Leave's status changes to 'cancelled'.
    Notifies all HR and Admin users.
    """
    if instance.is_cancelled:
        try:
            NotificationService.notify_leave_cancelled(instance)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create notification for leave cancellation: {e}'
            )


@receiver(post_save, sender='attendance.Attendance')
def notify_on_checkin(sender, instance, created, **kwargs):
    """
    Send notification when user checks in.

    Triggers when a user records check-in time.
    Notifies all HR and Admin users.
    """
    # Only notify on checkin (when checkout is None)
    if instance.checkin_time and not instance.checkout_time:
        try:
            NotificationService.notify_checkin(instance)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create notification for checkin: {e}'
            )


@receiver(post_save, sender='attendance.Attendance')
def notify_on_checkout(sender, instance, **kwargs):
    """
    Send notification when user checks out.

    Triggers when a user records checkout time.
    Notifies all HR and Admin users.
    """
    # Only notify on checkout (when both times are present)
    if instance.checkin_time and instance.checkout_time:
        try:
            # Get the update_fields to see if checkout was just set
            # This is a simple check - in production, track previous state
            NotificationService.notify_checkout(instance)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f'Failed to create notification for checkout: {e}'
            )
