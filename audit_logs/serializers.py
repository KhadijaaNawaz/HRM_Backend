"""
Serializers for audit log models.
"""

from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'action', 'target_model', 'target_id',
            'meta', 'ip_address', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class AuditLogDetailSerializer(AuditLogSerializer):
    """Detailed serializer for AuditLog with additional context."""

    class Meta(AuditLogSerializer.Meta):
        fields = AuditLogSerializer.Meta.fields
