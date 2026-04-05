"""
Admin configuration for notifications app.
"""

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model."""

    list_display = ['id', 'user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['id', 'created_at', 'read_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        """Disable manual creation through admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Allow only marking as read/unread."""
        return True

    def has_delete_permission(self, request, obj=None):
        """Allow deletion."""
        return True
