"""
Views for notification system.

Handles notification retrieval, marking as read/unread,
and notification statistics.
"""

from django.db.models import Count, Q
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationDetailSerializer,
    MarkReadSerializer,
    MarkUnreadSerializer,
    UnreadCountSerializer,
    MarkAllReadSerializer
)
from .filters import NotificationFilter


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for notification management.

    - Users can only view their own notifications
    - Supports marking as read/unread
    - Provides unread count
    - Notifications are created via signals, not directly
    """

    serializer_class = NotificationDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NotificationFilter
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', '-created_at', 'is_read']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return only current user's notifications."""
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('user')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'unread_count':
            return UnreadCountSerializer
        return NotificationDetailSerializer

    @action(detail=True, methods=['post'], url_path='read')
    def mark_read(self, request, pk=None):
        """
        Mark a notification as read.

        Updates the is_read flag and sets the read_at timestamp.
        """
        notification = self.get_object()

        # Verify ownership
        if notification.user != request.user:
            return Response({
                'error': 'You can only manage your own notifications.'
            }, status=status.HTTP_403_FORBIDDEN)

        notification.mark_as_read()

        serializer = NotificationDetailSerializer(notification)
        return Response({
            'message': 'Notification marked as read.',
            'notification': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='unread')
    def mark_unread(self, request, pk=None):
        """
        Mark a notification as unread.

        Clears the is_read flag and read_at timestamp.
        """
        notification = self.get_object()

        # Verify ownership
        if notification.user != request.user:
            return Response({
                'error': 'You can only manage your own notifications.'
            }, status=status.HTTP_403_FORBIDDEN)

        notification.mark_as_unread()

        serializer = NotificationDetailSerializer(notification)
        return Response({
            'message': 'Notification marked as unread.',
            'notification': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='read-all')
    def mark_all_read(self, request):
        """
        Mark all notifications as read for the current user.

        Bulk updates all unread notifications.
        """
        user = request.user

        # Mark all unread notifications as read
        from django.utils import timezone
        updated_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return Response({
            'message': f'Marked {updated_count} notifications as read.',
            'updated_count': updated_count
        })

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Get the count of unread notifications for the current user.

        Returns the total number of unread notifications.
        """
        user = request.user

        unread_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()

        return Response({
            'unread_count': unread_count
        })

    @action(detail=False, methods=['delete'], url_path='clear-all')
    def clear_all(self, request):
        """
        Delete all read notifications for the current user.

        Permanently removes all notifications that have been read.
        """
        user = request.user

        # Delete all read notifications
        deleted_count = Notification.objects.filter(
            user=user,
            is_read=True
        ).delete()[0]

        return Response({
            'message': f'Deleted {deleted_count} read notifications.',
            'deleted_count': deleted_count
        })
