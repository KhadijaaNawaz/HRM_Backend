"""
Views for audit log management.

Handles viewing of audit logs for compliance purposes.
"""

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogDetailSerializer
from accounts.permissions import IsTenantAdmin
from .filters import AuditLogFilter


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.

    - Only tenant admins can view audit logs
    - Logs are ordered by newest first

    Filtering:
    - action: Action type (exact match)
    - action_contains: Action type (partial match)
    - user: User ID (UUID)
    - user_email: User email (partial match)
    - target_model: Target model (exact match)
    - target_id: Target object ID (partial match)
    - timestamp_after: Timestamp after (ISO datetime)
    - timestamp_before: Timestamp before (ISO datetime)
    - timestamp_days: Timestamp within X days ago
    - ip_address: IP address (partial match)
    - search: Global search across action, target_model, target_id

    Ordering:
    - ordering: Order by field (timestamp, -timestamp, action, -action)
    """
    serializer_class = AuditLogDetailSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ['action', 'target_model', 'target_id', 'user__email', 'ip_address']
    ordering_fields = ['timestamp', 'action']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Return audit logs for current tenant."""
        return AuditLog.objects.all().select_related('user')

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'retrieve':
            return AuditLogDetailSerializer
        return AuditLogSerializer
