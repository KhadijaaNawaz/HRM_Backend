"""
Serializers for attendance models.
"""

from rest_framework import serializers
from datetime import date, datetime, timedelta
from django.utils import timezone
from .models import Attendance, AttendanceStatus, AttendanceSettings


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    hours_worked = serializers.FloatField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'user_email', 'user_name', 'date',
            'checkin_time', 'checkout_time', 'hours_worked',
            'notes', 'location', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CheckinSerializer(serializers.Serializer):
    """Serializer for check-in request."""
    notes = serializers.CharField(required=False, allow_blank=True)
    location = serializers.DictField(required=False)

    def validate_location(self, value):
        """Validate location format."""
        if value:
            if 'lat' not in value or 'lng' not in value:
                raise serializers.ValidationError(
                    'Location must contain "lat" and "lng" keys.'
                )
        return value


class CheckoutSerializer(serializers.Serializer):
    """Serializer for check-out request."""
    notes = serializers.CharField(required=False, allow_blank=True)
    location = serializers.DictField(required=False)

    def validate_location(self, value):
        """Validate location format."""
        if value:
            if 'lat' not in value or 'lng' not in value:
                raise serializers.ValidationError(
                    'Location must contain "lat" and "lng" keys.'
                )
        return value


class MyAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for user's own attendance records."""
    hours_worked = serializers.FloatField(read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'date', 'checkin_time', 'checkout_time',
            'hours_worked', 'notes', 'location', 'status'
        ]


class MonthlyStatsSerializer(serializers.Serializer):
    """Serializer for monthly attendance statistics."""
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    total_days = serializers.IntegerField()
    working_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    half_days = serializers.IntegerField()
    late_days = serializers.IntegerField()
    total_hours = serializers.FloatField()
    average_hours_per_day = serializers.FloatField()


class AttendanceSettingsSerializer(serializers.ModelSerializer):
    """Serializer for attendance settings."""

    class Meta:
        model = AttendanceSettings
        fields = [
            'id', 'work_start_time', 'work_end_time',
            'grace_period_minutes', 'break_duration_minutes',
            'overtime_enabled', 'overtime_start_after_minutes'
        ]
