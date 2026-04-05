"""
Serializers for notification system.

Provides serializers for notification CRUD operations,
marking as read/unread, and notification statistics.
"""

from rest_framework import serializers
from .models import Notification, NotificationType


class NotificationSerializer(serializers.ModelSerializer):
    """Basic serializer for Notification model."""

    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'notification_type',
            'is_read', 'action_url', 'action_text', 'metadata',
            'created_at', 'read_at'
        ]
        read_only_fields = [
            'id', 'user', 'title', 'message', 'notification_type',
            'action_url', 'action_text', 'metadata', 'created_at', 'read_at'
        ]


class NotificationDetailSerializer(NotificationSerializer):
    """Detailed serializer for Notification with nested user information."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )

    class Meta(NotificationSerializer.Meta):
        fields = NotificationSerializer.Meta.fields + [
            'user_email', 'user_name', 'notification_type_display'
        ]


class MarkReadSerializer(serializers.Serializer):
    """Serializer for marking notification as read."""

    pass


class MarkUnreadSerializer(serializers.Serializer):
    """Serializer for marking notification as unread."""

    pass


class UnreadCountSerializer(serializers.Serializer):
    """Serializer for unread notification count."""

    unread_count = serializers.IntegerField(help_text="Total unread notifications")


class MarkAllReadSerializer(serializers.Serializer):
    """Serializer for marking all notifications as read."""

    pass
