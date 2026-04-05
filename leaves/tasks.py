"""
Celery tasks for leave-related email notifications.

Provides async email sending for leave events using Celery.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_leave_application_email(self, leave_id: str):
    """
    Send email to HR/Admin when leave is applied.

    Args:
        leave_id: UUID of the leave record

    Retries up to 3 times if sending fails.
    """
    from .models import Leave

    try:
        leave = Leave.objects.get(id=leave_id)

        # Get all HR and Admin users
        from accounts.models import Role
        from django.contrib.auth import get_user_model

        User = get_user_model()
        hr_roles = Role.objects.filter(name__in=['HR', 'HR Manager'])
        hr_users = list(User.objects.filter(
            is_tenant_admin=True
        ).values_list('email', flat=True)) + list(User.objects.filter(
            user_roles__role__in=hr_roles
        ).values_list('email', flat=True))

        # Remove duplicates and filter out empty emails
        to_emails = list(set([email for email in hr_users if email]))

        if not to_emails:
            return {'status': 'skipped', 'reason': 'No recipients found'}

        # Prepare context
        context = {
            'employee_name': leave.employee.get_full_name() or leave.employee.email,
            'employee_email': leave.employee.email,
            'leave_type': leave.get_leave_type_display(),
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'days': leave.days,
            'reason': leave.reason or 'No reason provided',
            'leave_url': f'{settings.FRONTEND_URL}/leaves/{leave.id}' if hasattr(settings, 'FRONTEND_URL') else '',
        }

        # Render email templates
        subject = f'New Leave Request: {context["employee_name"]}'
        message_plain = render_to_string('emails/leave_applied.txt', context)
        message_html = render_to_string('emails/leave_applied.html', context)

        # Send email
        send_mail(
            subject=subject,
            message=message_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=to_emails,
            html_message=message_html,
            fail_silently=False
        )

        return {'status': 'sent', 'recipients': to_emails}

    except Leave.DoesNotExist:
        return {'status': 'error', 'reason': 'Leave not found'}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_leave_approval_email(self, leave_id: str):
    """
    Send email to employee when leave is approved.

    Args:
        leave_id: UUID of the leave record

    Retries up to 3 times if sending fails.
    """
    from .models import Leave

    try:
        leave = Leave.objects.get(id=leave_id)

        if not leave.employee.email:
            return {'status': 'skipped', 'reason': 'Employee has no email'}

        # Prepare context
        context = {
            'employee_name': leave.employee.get_full_name() or leave.employee.email,
            'leave_type': leave.get_leave_type_display(),
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'days': leave.days,
            'approver_name': leave.approved_by.get_full_name() or leave.approved_by.email,
            'approval_comment': leave.approval_comment or 'No comment provided',
            'leave_url': f'{settings.FRONTEND_URL}/leaves/{leave.id}' if hasattr(settings, 'FRONTEND_URL') else '',
        }

        # Render email templates
        subject = f'Your Leave Request has been Approved'
        message_plain = render_to_string('emails/leave_approved.txt', context)
        message_html = render_to_string('emails/leave_approved.html', context)

        # Send email
        send_mail(
            subject=subject,
            message=message_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[leave.employee.email],
            html_message=message_html,
            fail_silently=False
        )

        return {'status': 'sent', 'recipient': leave.employee.email}

    except Leave.DoesNotExist:
        return {'status': 'error', 'reason': 'Leave not found'}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_leave_rejection_email(self, leave_id: str):
    """
    Send email to employee when leave is rejected.

    Args:
        leave_id: UUID of the leave record

    Retries up to 3 times if sending fails.
    """
    from .models import Leave

    try:
        leave = Leave.objects.get(id=leave_id)

        if not leave.employee.email:
            return {'status': 'skipped', 'reason': 'Employee has no email'}

        # Prepare context
        context = {
            'employee_name': leave.employee.get_full_name() or leave.employee.email,
            'leave_type': leave.get_leave_type_display(),
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'days': leave.days,
            'rejecter_name': leave.rejected_by.get_full_name() or leave.rejected_by.email,
            'rejection_reason': leave.rejection_reason or 'No reason provided',
            'leave_url': f'{settings.FRONTEND_URL}/leaves/{leave.id}' if hasattr(settings, 'FRONTEND_URL') else '',
        }

        # Render email templates
        subject = f'Your Leave Request has been Rejected'
        message_plain = render_to_string('emails/leave_rejected.txt', context)
        message_html = render_to_string('emails/leave_rejected.html', context)

        # Send email
        send_mail(
            subject=subject,
            message=message_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[leave.employee.email],
            html_message=message_html,
            fail_silently=False
        )

        return {'status': 'sent', 'recipient': leave.employee.email}

    except Leave.DoesNotExist:
        return {'status': 'error', 'reason': 'Leave not found'}
    except Exception as e:
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_leave_cancellation_email(self, leave_id: str):
    """
    Send email to HR/Admin when leave is cancelled.

    Args:
        leave_id: UUID of the leave record

    Retries up to 3 times if sending fails.
    """
    from .models import Leave

    try:
        leave = Leave.objects.get(id=leave_id)

        # Get all HR and Admin users
        from accounts.models import Role
        from django.contrib.auth import get_user_model

        User = get_user_model()
        hr_roles = Role.objects.filter(name__in=['HR', 'HR Manager'])
        hr_users = list(User.objects.filter(
            is_tenant_admin=True
        ).values_list('email', flat=True)) + list(User.objects.filter(
            user_roles__role__in=hr_roles
        ).values_list('email', flat=True))

        # Remove duplicates and filter out empty emails
        to_emails = list(set([email for email in hr_users if email]))

        if not to_emails:
            return {'status': 'skipped', 'reason': 'No recipients found'}

        # Prepare context
        context = {
            'employee_name': leave.employee.get_full_name() or leave.employee.email,
            'employee_email': leave.employee.email,
            'leave_type': leave.get_leave_type_display(),
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'days': leave.days,
            'leave_url': f'{settings.FRONTEND_URL}/leaves/{leave.id}' if hasattr(settings, 'FRONTEND_URL') else '',
        }

        # Render email templates
        subject = f'Leave Cancelled: {context["employee_name"]}'
        message_plain = render_to_string('emails/leave_cancelled.txt', context)
        message_html = render_to_string('emails/leave_cancelled.html', context)

        # Send email
        send_mail(
            subject=subject,
            message=message_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=to_emails,
            html_message=message_html,
            fail_silently=False
        )

        return {'status': 'sent', 'recipients': to_emails}

    except Leave.DoesNotExist:
        return {'status': 'error', 'reason': 'Leave not found'}
    except Exception as e:
        raise self.retry(exc=e)
