"""
Notification service for creating notifications.

Provides centralized notification creation service
for all tenant events.
"""

from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model

from .models import Notification, NotificationType

User = get_user_model()


class NotificationService:
    """
    Service class for creating notifications.

    Provides static methods for creating different types of notifications
    based on events in the system.
    """

    @staticmethod
    def create_notification(
        user: User,
        title: str,
        message: str,
        notification_type: str = NotificationType.INFO,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a notification for a user.

        Args:
            user: The user who will receive the notification
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (default: INFO)
            action_url: Optional URL for action button
            action_text: Optional text for action button
            metadata: Optional metadata dictionary

        Returns:
            The created Notification instance
        """
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url or '',
            action_text=action_text or '',
            metadata=metadata or {}
        )
        return notification

    @staticmethod
    def create_bulk_notifications(
        users: List[User],
        title: str,
        message: str,
        notification_type: str = NotificationType.INFO,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Notification]:
        """
        Create notifications for multiple users.

        Args:
            users: List of users who will receive the notification
            title: Notification title
            message: Notification message content
            notification_type: Type of notification (default: INFO)
            action_url: Optional URL for action button
            action_text: Optional text for action button
            metadata: Optional metadata dictionary

        Returns:
            List of created Notification instances
        """
        notifications = []
        for user in users:
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url or '',
                action_text=action_text or '',
                metadata=metadata or {}
            )
            notifications.append(notification)
        return notifications

    @staticmethod
    def notify_leave_applied(leave) -> Notification:
        """
        Notify HR/Admin when a new leave is applied.

        Args:
            leave: The Leave instance

        Returns:
            List of created notifications for all HR/Admin users
        """
        from accounts.models import UserRole, Role

        # Get all HR and Admin users
        hr_roles = Role.objects.filter(name__in=['HR', 'HR Manager'])
        hr_users = User.objects.filter(
            is_tenant_admin=True
        ) | User.objects.filter(
            user_roles__role__in=hr_roles
        )
        hr_users = hr_users.distinct()

        employee_name = leave.employee.get_full_name() or leave.employee.email
        title = f'New Leave Request: {employee_name}'
        message = (
            f'{employee_name} has applied for {leave.get_leave_type_display()} '
            f'from {leave.start_date} to {leave.end_date} ({leave.days} days). '
            f'Reason: {leave.reason or "No reason provided"}'
        )

        notifications = []
        for user in hr_users:
            notification = NotificationService.create_notification(
                user=user,
                title=title,
                message=message,
                notification_type=NotificationType.LEAVE_APPLIED,
                action_url=f'/leaves/{leave.id}',
                action_text='View Leave',
                metadata={
                    'leave_id': str(leave.id),
                    'employee_id': str(leave.employee.id),
                    'leave_type': leave.leave_type,
                    'start_date': str(leave.start_date),
                    'end_date': str(leave.end_date),
                    'days': leave.days
                }
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def notify_leave_approved(leave) -> Notification:
        """
        Notify employee when their leave is approved.

        Args:
            leave: The Leave instance

        Returns:
            The created notification
        """
        employee_name = leave.employee.get_full_name() or leave.employee.email
        approver_name = leave.approved_by.get_full_name() or leave.approved_by.email

        title = f'Leave Approved: {leave.get_leave_type_display()}'
        message = (
            f'Your {leave.get_leave_type_display()} from {leave.start_date} '
            f'to {leave.end_date} ({leave.days} days) has been approved by {approver_name}.'
        )

        notification = NotificationService.create_notification(
            user=leave.employee,
            title=title,
            message=message,
            notification_type=NotificationType.LEAVE_APPROVED,
            action_url=f'/leaves/{leave.id}',
            action_text='View Leave',
            metadata={
                'leave_id': str(leave.id),
                'approved_by': str(leave.approved_by.id),
                'approved_at': leave.approved_at.isoformat() if leave.approved_at else None
            }
        )

        return notification

    @staticmethod
    def notify_leave_rejected(leave) -> Notification:
        """
        Notify employee when their leave is rejected.

        Args:
            leave: The Leave instance

        Returns:
            The created notification
        """
        employee_name = leave.employee.get_full_name() or leave.employee.email
        rejecter_name = leave.rejected_by.get_full_name() or leave.rejected_by.email

        title = f'Leave Rejected: {leave.get_leave_type_display()}'
        message = (
            f'Your {leave.get_leave_type_display()} from {leave.start_date} '
            f'to {leave.end_date} ({leave.days} days) has been rejected by {rejecter_name}. '
            f'Reason: {leave.rejection_reason or "No reason provided"}'
        )

        notification = NotificationService.create_notification(
            user=leave.employee,
            title=title,
            message=message,
            notification_type=NotificationType.LEAVE_REJECTED,
            action_url=f'/leaves/{leave.id}',
            action_text='View Leave',
            metadata={
                'leave_id': str(leave.id),
                'rejected_by': str(leave.rejected_by.id),
                'rejected_at': leave.rejected_at.isoformat() if leave.rejected_at else None,
                'rejection_reason': leave.rejection_reason
            }
        )

        return notification

    @staticmethod
    def notify_leave_cancelled(leave) -> List[Notification]:
        """
        Notify HR/Admin when a leave is cancelled.

        Args:
            leave: The Leave instance

        Returns:
            List of created notifications for all HR/Admin users
        """
        from accounts.models import UserRole, Role

        # Get all HR and Admin users
        hr_roles = Role.objects.filter(name__in=['HR', 'HR Manager'])
        hr_users = User.objects.filter(
            is_tenant_admin=True
        ) | User.objects.filter(
            user_roles__role__in=hr_roles
        )
        hr_users = hr_users.distinct()

        employee_name = leave.employee.get_full_name() or leave.employee.email
        title = f'Leave Cancelled: {employee_name}'
        message = (
            f'{employee_name} has cancelled their {leave.get_leave_type_display()} '
            f'from {leave.start_date} to {leave.end_date} ({leave.days} days).'
        )

        notifications = []
        for user in hr_users:
            notification = NotificationService.create_notification(
                user=user,
                title=title,
                message=message,
                notification_type=NotificationType.LEAVE_CANCELLED,
                action_url=f'/leaves/{leave.id}',
                action_text='View Leave',
                metadata={
                    'leave_id': str(leave.id),
                    'employee_id': str(leave.employee.id),
                    'leave_type': leave.leave_type
                }
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def notify_checkin(attendance) -> List[Notification]:
        """
        Notify HR/Admin when a user checks in.

        Args:
            attendance: The Attendance instance

        Returns:
            List of created notifications for all HR/Admin users
        """
        from accounts.models import UserRole, Role

        # Get all HR and Admin users
        hr_roles = Role.objects.filter(name__in=['HR', 'HR Manager'])
        hr_users = User.objects.filter(
            is_tenant_admin=True
        ) | User.objects.filter(
            user_roles__role__in=hr_roles
        )
        hr_users = hr_users.distinct()

        user_name = attendance.user.get_full_name() or attendance.user.email
        title = f'Check-in: {user_name}'
        message = (
            f'{user_name} checked in at {attendance.checkin_time.strftime("%H:%M")} '
            f'on {attendance.date}.'
        )

        notifications = []
        for user in hr_users:
            notification = NotificationService.create_notification(
                user=user,
                title=title,
                message=message,
                notification_type=NotificationType.CHECKIN,
                action_url=f'/attendance/{attendance.id}',
                action_text='View Attendance',
                metadata={
                    'attendance_id': str(attendance.id),
                    'user_id': str(attendance.user.id),
                    'date': str(attendance.date),
                    'checkin_time': attendance.checkin_time.isoformat() if attendance.checkin_time else None
                }
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def notify_checkout(attendance) -> List[Notification]:
        """
        Notify HR/Admin when a user checks out.

        Args:
            attendance: The Attendance instance

        Returns:
            List of created notifications for all HR/Admin users
        """
        from accounts.models import UserRole, Role

        # Get all HR and Admin users
        hr_roles = Role.objects.filter(name__in=['HR', 'HR Manager'])
        hr_users = User.objects.filter(
            is_tenant_admin=True
        ) | User.objects.filter(
            user_roles__role__in=hr_roles
        )
        hr_users = hr_users.distinct()

        user_name = attendance.user.get_full_name() or attendance.user.email
        title = f'Check-out: {user_name}'
        message = (
            f'{user_name} checked out at {attendance.checkout_time.strftime("%H:%M")} '
            f'on {attendance.date}.'
        )

        notifications = []
        for user in hr_users:
            notification = NotificationService.create_notification(
                user=user,
                title=title,
                message=message,
                notification_type=NotificationType.CHECKOUT,
                action_url=f'/attendance/{attendance.id}',
                action_text='View Attendance',
                metadata={
                    'attendance_id': str(attendance.id),
                    'user_id': str(attendance.user.id),
                    'date': str(attendance.date),
                    'checkout_time': attendance.checkout_time.isoformat() if attendance.checkout_time else None
                }
            )
            notifications.append(notification)

        return notifications
