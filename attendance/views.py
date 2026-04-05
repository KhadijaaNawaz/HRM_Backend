"""
Views for attendance tracking.

Handles check-in/check-out, attendance history,
and monthly statistics.
"""

from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Q, Count, F
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Attendance, AttendanceStatus, AttendanceSettings
from .serializers import (
    AttendanceSerializer,
    CheckinSerializer,
    CheckoutSerializer,
    MyAttendanceSerializer,
    MonthlyStatsSerializer,
    AttendanceSettingsSerializer
)
from .filters import AttendanceFilter
from accounts.permissions import IsHROrAdmin, IsTenantAdmin


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


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for attendance management.

    - Employees see only their own records
    - HR/Admin can see all records

    Filtering:
    - date: Exact date match (YYYY-MM-DD)
    - date_gte: Date from (inclusive)
    - date_lte: Date to (inclusive)
    - status: Attendance status (present, absent, half_day, late)
    - user: User ID (UUID)
    - user_email: User email (exact match)
    - month: Month number (1-12)
    - year: Year (YYYY)
    - has_checkin: Filter by check-in presence (true/false)
    - today: Show only today's records (true)
    - this_week: Show only this week's records (true)
    - this_month: Show only this month's records (true)
    - search: Search across user email, names, notes

    Ordering:
    - ordering: Order by field (date, -date, checkin_time, -checkin_time, created_at, -created_at)
    """
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AttendanceFilter
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'notes']
    ordering_fields = ['date', 'checkin_time', 'checkout_time', 'created_at']
    ordering = ['-date', '-checkin_time']

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user

        # Tenant admins and HR see all attendance
        if user.is_tenant_admin or user.roles.filter(name__in=['HR', 'HR Manager']).exists():
            return Attendance.objects.all().select_related('user')

        # Regular users see only their own attendance
        return Attendance.objects.filter(user=user).select_related('user')

    @action(detail=False, methods=['post'], url_path='checkin')
    def checkin(self, request):
        """
        Check in for the day.

        Creates a new attendance record for today if one doesn't exist.
        Returns error if already checked in.
        """
        serializer = CheckinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        now = timezone.now()
        today = now.date()

        # Check if already checked in today
        existing_attendance = Attendance.objects.filter(
            user=user,
            date=today
        ).first()

        if existing_attendance:
            if existing_attendance.checkin_time:
                return Response({
                    'error': 'Already checked in today.',
                    'attendance_id': str(existing_attendance.id),
                    'checkin_time': existing_attendance.checkin_time
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Update existing record with check-in
                existing_attendance.checkin_time = timezone.now()
                existing_attendance.location = serializer.validated_data.get('location')
                existing_attendance.notes = serializer.validated_data.get('notes', '')
                existing_attendance.save()

                # Log check-in
                create_audit_log(
                    user, 'attendance.checkin', 'Attendance', existing_attendance.id,
                    ip_address=self.get_client_ip(request)
                )

                return Response({
                    'attendance_id': str(existing_attendance.id),
                    'timestamp': existing_attendance.checkin_time,
                    'message': 'Checked in successfully'
                }, status=status.HTTP_201_CREATED)

        # Create new attendance record
        attendance = Attendance.objects.create(
            user=user,
            date=today,
            checkin_time=now,
            location=serializer.validated_data.get('location'),
            notes=serializer.validated_data.get('notes', '')
        )

        # Log check-in
        create_audit_log(
            user, 'attendance.checkin', 'Attendance', attendance.id,
            ip_address=self.get_client_ip(request)
        )

        return Response({
            'attendance_id': str(attendance.id),
            'timestamp': attendance.checkin_time,
            'message': 'Checked in successfully'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """
        Check out for the day.

        Updates the attendance record with checkout time.
        Returns error if not checked in.
        """
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        now = timezone.now()
        today = now.date()

        # Find today's attendance record
        attendance = Attendance.objects.filter(
            user=user,
            date=today
        ).first()

        if not attendance:
            return Response({
                'error': 'No check-in found for today.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not attendance.checkin_time:
            return Response({
                'error': 'Must check in before checking out.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if attendance.checkout_time:
            return Response({
                'error': 'Already checked out today.',
                'checkout_time': attendance.checkout_time
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update with checkout time
        attendance.checkout_time = now
        attendance.notes = serializer.validated_data.get('notes', attendance.notes)
        if serializer.validated_data.get('location'):
            attendance.location = serializer.validated_data.get('location')
        attendance.save()

        # Log check-out
        create_audit_log(
            user, 'attendance.checkout', 'Attendance', attendance.id,
            ip_address=self.get_client_ip(request),
            meta={'hours_worked': attendance.hours_worked}
        )

        return Response({
            'attendance_id': str(attendance.id),
            'checkin': attendance.checkin_time,
            'checkout': attendance.checkout_time,
            'hours_worked': attendance.hours_worked,
            'message': 'Checked out successfully'
        })

    @action(detail=False, methods=['get'], url_path='my-attendance')
    def my_attendance(self, request):
        """
        Get current user's attendance history.

        Query params:
        - start_date: Filter from date (YYYY-MM-DD)
        - end_date: Filter to date (YYYY-MM-DD)
        """
        user = request.user
        queryset = Attendance.objects.filter(user=user)

        # Apply date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            try:
                queryset = queryset.filter(date__gte=datetime.strptime(start_date, '%Y-%m-%d').date())
            except ValueError:
                return Response({
                    'error': 'Invalid start_date format. Use YYYY-MM-DD.'
                }, status=status.HTTP_400_BAD_REQUEST)

        if end_date:
            try:
                queryset = queryset.filter(date__lte=datetime.strptime(end_date, '%Y-%m-%d').date())
            except ValueError:
                return Response({
                    'error': 'Invalid end_date format. Use YYYY-MM-DD.'
                }, status=status.HTTP_400_BAD_REQUEST)

        queryset = queryset.order_by('-date')

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MyAttendanceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MyAttendanceSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my-monthly-stats')
    def my_monthly_stats(self, request):
        """
        Get monthly attendance statistics for current user.

        Query params:
        - month: Month number (1-12), defaults to current month
        - year: Year, defaults to current year
        """
        user = request.user

        # Get month and year from query params or use current date
        current_date = timezone.now().date()
        month = int(request.query_params.get('month', current_date.month))
        year = int(request.query_params.get('year', current_date.year))

        # Validate month
        if not 1 <= month <= 12:
            return Response({
                'error': 'Month must be between 1 and 12.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Calculate date range
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        # Get attendance records for the month
        attendances = Attendance.objects.filter(
            user=user,
            date__gte=first_day,
            date__lte=last_day
        )

        # Calculate statistics
        total_days = (last_day - first_day).days + 1
        working_days = len([d for d in range(1, last_day.day + 1) if date(year, month, d).weekday() < 5])  # Mon-Fri

        present_days = attendances.filter(checkin_time__isnull=False).count()
        absent_days = working_days - present_days

        # Calculate status counts
        half_days = attendances.filter(status=AttendanceStatus.HALF_DAY).count()
        late_days = attendances.filter(status=AttendanceStatus.LATE).count()

        # Calculate total hours
        total_hours = sum(
            a.hours_worked for a in attendances
            if a.hours_worked is not None
        )

        average_hours = total_hours / present_days if present_days > 0 else 0

        return Response({
            'month': month,
            'year': year,
            'total_days': total_days,
            'working_days': working_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'half_days': half_days,
            'late_days': late_days,
            'total_hours': round(total_hours, 2),
            'average_hours_per_day': round(average_hours, 2)
        })

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AttendanceSettingsView(APIView):
    """
    Get and update attendance settings.

    Only tenant admins can update settings.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current organization attendance settings."""
        settings = AttendanceSettings.objects.first()
        if not settings:
            # Create default settings
            settings = AttendanceSettings.objects.create()

        serializer = AttendanceSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        """Update attendance settings (admin only)."""
        if not request.user.is_tenant_admin:
            return Response(
                {'error': 'Only tenant admins can update attendance settings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        settings = AttendanceSettings.objects.first()
        if not settings:
            settings = AttendanceSettings.objects.create()

        serializer = AttendanceSettingsSerializer(
            settings,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
