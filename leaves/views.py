"""
Views for leave management.

Handles leave CRUD operations, approval workflows, and leave statistics.
"""

from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Q, Count, F, Case, When
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Leave, LeaveBalance, LeaveType, LeaveStatus
from .serializers import (
    LeaveSerializer, LeaveDetailSerializer, CreateLeaveSerializer,
    ApproveLeaveSerializer, RejectLeaveSerializer, CancelLeaveSerializer,
    LeaveBalanceSerializer, MyLeaveSerializer, LeaveSummarySerializer,
    LeaveBalanceSummarySerializer
)
from .permissions import IsOwnerOrHROrAdmin, CanApproveLeave, IsLeaveOwner
from .filters import LeaveFilter, LeaveBalanceFilter
from accounts.permissions import IsHROrAdmin


def create_audit_log(user, action, target_model, target_id, ip_address=None, meta=None):
    """Helper function to create audit logs with error handling."""
    try:
        from audit_logs.models import AuditLog
        AuditLog.objects.create(
            user=user,
            action=action,
            target_model=target_model,
            target_id=str(target_id),
            ip_address=ip_address,
            meta=meta or {}
        )
    except:
        pass  # Audit logs not available in this schema


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LeaveViewSet(viewsets.ModelViewSet):
    """
    ViewSet for leave management.

    - Employees can create and view only their own leaves
    - HR/Admin can view all leaves and approve/reject
    - Supports filtering, searching, and pagination
    """
    serializer_class = LeaveDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeaveFilter
    search_fields = ['reason', 'employee__email', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['start_date', '-start_date', 'end_date', '-created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user

        # HR/Admin see all leaves
        if user.is_tenant_admin or user.roles.filter(name__in=['HR', 'HR Manager']).exists():
            return Leave.objects.all().select_related('employee', 'approved_by', 'rejected_by')

        # Employees see only their own leaves
        return Leave.objects.filter(employee=user).select_related('employee', 'approved_by', 'rejected_by')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CreateLeaveSerializer
        elif self.action in ['my_leaves']:
            return MyLeaveSerializer
        return LeaveDetailSerializer

    def perform_create(self, serializer):
        """Create leave and send notification."""
        leave = serializer.save(employee=self.request.user)

        # Log leave creation
        create_audit_log(
            self.request.user, 'leave.created', 'Leave', leave.id,
            ip_address=get_client_ip(self.request),
            meta={
                'leave_type': leave.leave_type,
                'start_date': str(leave.start_date),
                'end_date': str(leave.end_date),
                'days': leave.days
            }
        )

        # Send notification to HR/Admin (will be handled by signals)
        try:
            from notifications.services import NotificationService
            NotificationService.notify_leave_applied(leave)
        except:
            pass  # Notifications not available yet

        return leave

    def perform_update(self, serializer):
        """Update leave and log changes."""
        leave = serializer.save()

        # Log leave update
        create_audit_log(
            self.request.user, 'leave.updated', 'Leave', leave.id,
            ip_address=get_client_ip(self.request)
        )

        return leave

    def perform_destroy(self, instance):
        """Soft delete leave (cancel)."""
        # Use cancel action instead
        instance.cancel()

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approve a leave request.

        Only HR/Admin can approve leaves.
        Sends notification to employee upon approval.
        """
        leave = self.get_object()

        # Validate leave is pending
        if not leave.is_pending:
            return Response({
                'error': f'Only pending leaves can be approved. Current status: {leave.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate permissions
        if not request.user.is_tenant_admin:
            if not request.user.roles.filter(name__in=['HR', 'HR Manager']).exists():
                return Response({
                    'error': 'Only HR and Admin users can approve leaves.'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = ApproveLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Approve the leave
        leave.approve(approver=request.user, comment=serializer.validated_data.get('comment', ''))

        # Log approval
        create_audit_log(
            request.user, 'leave.approved', 'Leave', leave.id,
            ip_address=get_client_ip(request),
            meta={
                'employee_email': leave.employee.email,
                'leave_type': leave.leave_type,
                'days': leave.days
            }
        )

        # Send notification to employee
        try:
            from notifications.services import NotificationService
            NotificationService.notify_leave_approved(leave)
        except:
            pass  # Notifications not available yet

        # Send email (async)
        try:
            from .tasks import send_leave_approval_email
            send_leave_approval_email.delay(str(leave.id))
        except:
            pass  # Celery not configured

        serializer = LeaveDetailSerializer(leave)
        return Response({
            'message': f'Leave request approved successfully.',
            'leave': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """
        Reject a leave request.

        Only HR/Admin can reject leaves.
        Requires a reason for rejection.
        Sends notification to employee.
        """
        leave = self.get_object()

        # Validate leave is pending
        if not leave.is_pending:
            return Response({
                'error': f'Only pending leaves can be rejected. Current status: {leave.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate permissions
        if not request.user.is_tenant_admin:
            if not request.user.roles.filter(name__in=['HR', 'HR Manager']).exists():
                return Response({
                    'error': 'Only HR and Admin users can reject leaves.'
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = RejectLeaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Reject the leave
        leave.reject(rejecter=request.user, reason=serializer.validated_data['reason'])

        # Log rejection
        create_audit_log(
            request.user, 'leave.rejected', 'Leave', leave.id,
            ip_address=get_client_ip(request),
            meta={
                'employee_email': leave.employee.email,
                'leave_type': leave.leave_type,
                'days': leave.days,
                'rejection_reason': serializer.validated_data['reason']
            }
        )

        # Send notification to employee
        try:
            from notifications.services import NotificationService
            NotificationService.notify_leave_rejected(leave)
        except:
            pass  # Notifications not available yet

        # Send email (async)
        try:
            from .tasks import send_leave_rejection_email
            send_leave_rejection_email.delay(str(leave.id))
        except:
            pass  # Celery not configured

        serializer = LeaveDetailSerializer(leave)
        return Response({
            'message': f'Leave request rejected successfully.',
            'leave': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel a leave request.

        Employees can cancel their own pending or approved leaves.
        """
        leave = self.get_object()

        # Validate permissions (can only cancel own leaves unless HR/Admin)
        if not request.user.is_tenant_admin:
            if not request.user.roles.filter(name__in=['HR', 'HR Manager']).exists():
                if leave.employee != request.user:
                    return Response({
                        'error': 'You can only cancel your own leaves.'
                    }, status=status.HTTP_403_FORBIDDEN)

        try:
            # Validate leave can be cancelled
            leave.cancel()
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Log cancellation
        create_audit_log(
            request.user, 'leave.cancelled', 'Leave', leave.id,
            ip_address=get_client_ip(request),
            meta={
                'employee_email': leave.employee.email,
                'leave_type': leave.leave_type,
                'days': leave.days
            }
        )

        # Send notification to HR/Admin about cancellation
        try:
            from notifications.services import NotificationService
            NotificationService.notify_leave_cancelled(leave)
        except:
            pass  # Notifications not available yet

        serializer = LeaveDetailSerializer(leave)
        return Response({
            'message': 'Leave cancelled successfully.',
            'leave': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='my-leaves')
    def my_leaves(self, request):
        """
        Get current user's leave requests.

        Supports optional filtering by query parameters.
        Query params:
        - status: Filter by status (pending, approved, rejected, cancelled)
        - year: Filter by year
        - leave_type: Filter by leave type
        """
        user = request.user
        queryset = Leave.objects.filter(employee=user)

        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        year_filter = request.query_params.get('year')
        if year_filter:
            try:
                queryset = queryset.filter(start_date__year=int(year_filter))
            except ValueError:
                return Response({
                    'error': 'Invalid year format. Use integer.'
                }, status=status.HTTP_400_BAD_REQUEST)

        leave_type_filter = request.query_params.get('leave_type')
        if leave_type_filter:
            queryset = queryset.filter(leave_type=leave_type_filter)

        queryset = queryset.order_by('-created_at')

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MyLeaveSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MyLeaveSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Get leave summary statistics.

        Provides breakdown of leaves by status and type.
        Only accessible to HR and Admin users.
        Query params:
        - year: Filter by year (default: current year)
        - month: Filter by month (1-12)
        """
        # Check permissions
        if not (request.user.is_tenant_admin or request.user.roles.filter(name__in=['HR', 'HR Manager']).exists()):
            return Response({
                'error': 'Only HR and Admin users can access leave summary.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get year/month from query params or use current date
        current_date = timezone.now().date()
        year = int(request.query_params.get('year', current_date.year))
        month = request.query_params.get('month')

        # Base queryset
        queryset = Leave.objects.all()

        # Apply year filter
        queryset = queryset.filter(start_date__year=year)

        # Apply month filter if provided
        if month:
            try:
                month_int = int(month)
                if not 1 <= month_int <= 12:
                    return Response({
                        'error': 'Month must be between 1 and 12.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                queryset = queryset.filter(start_date__month=month_int)
            except ValueError:
                return Response({
                    'error': 'Invalid month format.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate statistics
        total_leaves = queryset.count()
        pending_leaves = queryset.filter(status=LeaveStatus.PENDING).count()
        approved_leaves = queryset.filter(status=LeaveStatus.APPROVED).count()
        rejected_leaves = queryset.filter(status=LeaveStatus.REJECTED).count()
        cancelled_leaves = queryset.filter(status=LeaveStatus.CANCELLED).count()

        # Breakdown by leave type
        by_type = {}
        for leave_type_choice in LeaveType.choices:
            type_code = leave_type[0]
            type_name = leave_type[1]
            count = queryset.filter(leave_type=type_code).count()
            by_type[type_code] = {
                'name': type_name,
                'count': count
            }

        # This month's stats (if month was provided)
        this_month_pending = 0
        this_month_approved = 0
        this_month_rejected = 0

        if month:
            this_month_leaves = queryset.filter(start_date__month=month)
            this_month_pending = this_month_leaves.filter(status=LeaveStatus.PENDING).count()
            this_month_approved = this_month_leaves.filter(status=LeaveStatus.APPROVED).count()
            this_month_rejected = this_month_leaves.filter(status=LeaveStatus.REJECTED).count()

        # Upcoming leaves (approved in future)
        upcoming_leaves = queryset.filter(
            status=LeaveStatus.APPROVED,
            start_date__gt=timezone.now().date()
        ).count()

        return Response({
            'year': year,
            'month': month,
            'total_leaves': total_leaves,
            'pending_leaves': pending_leaves,
            'approved_leaves': approved_leaves,
            'rejected_leaves': rejected_leaves,
            'cancelled_leaves': cancelled_leaves,
            'by_type': by_type,
            'this_month_pending': this_month_pending,
            'this_month_approved': this_month_approved,
            'this_month_rejected': this_month_rejected,
            'upcoming_leaves': upcoming_leaves
        })

    @action(detail=False, methods=['get'], url_path='balance')
    def balance(self, request):
        """
        Get current user's leave balance.

        Returns balance for all leave types for current year.
        Query params:
        - year: Filter by year (default: current year)
        - leave_type: Filter by leave type
        """
        user = request.user
        current_date = timezone.now().date()
        year = int(request.query_params.get('year', current_date.year))
        leave_type = request.query_params.get('leave_type')

        # Get balances
        queryset = LeaveBalance.objects.filter(
            employee=user,
            year=year
        ).select_related('employee')

        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)

        serializer = LeaveBalanceSerializer(queryset, many=True)
        return Response({
            'year': year,
            'employee_email': user.email,
            'balances': serializer.data
        })


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing leave balances.

    HR/Admin can view all employee balances.
    Employees can only view their own balances.
    """
    serializer_class = LeaveBalanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LeaveBalanceFilter
    search_fields = ['employee__email', 'employee__first_name', 'employee__last_name']
    ordering_fields = ['leave_type', 'year', '-balance_days']
    ordering = ['year', 'leave_type']

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user

        # HR/Admin see all balances
        if user.is_tenant_admin or user.roles.filter(name__in=['HR', 'HR Manager']).exists():
            return LeaveBalance.objects.all().select_related('employee')

        # Employees see only their own balances
        return LeaveBalance.objects.filter(employee=user).select_related('employee')
