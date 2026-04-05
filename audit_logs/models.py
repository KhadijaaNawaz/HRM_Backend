"""
Audit logging models for HRM SaaS.

This module defines the AuditLog model for tracking all
important actions within the system for compliance purposes.
"""

import uuid
from django.db import models


class AuditLog(models.Model):
    """
    Audit log entry for tracking system actions.

    Records all important user and system actions for compliance
    and security auditing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    # Action details
    action = models.CharField(max_length=100)  # e.g., "user.login", "user.created"
    target_model = models.CharField(max_length=50, null=True, blank=True)  # Model name
    target_id = models.CharField(max_length=100, null=True, blank=True)  # ID of target object

    # Additional metadata
    meta = models.JSONField(default=dict, blank=True)  # Additional action details
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        user_display = self.user.email if self.user else 'System'
        return f"{user_display} - {self.action} at {self.timestamp}"
