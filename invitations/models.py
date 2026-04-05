"""
Invitation models for HRM SaaS.

This module defines the Invitation model for email-based user invitations.
"""

import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator


class InvitationStatus(models.TextChoices):
    """Invitation status choices."""
    PENDING = 'pending', 'Pending'
    ACCEPTED = 'accepted', 'Accepted'
    CANCELLED = 'cancelled', 'Cancelled'
    EXPIRED = 'expired', 'Expired'


class Invitation(models.Model):
    """
    Email invitation for new users.

    Allows HR/Admin to invite users via email with a secure token.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Invitation details
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # User information (to be created on acceptance)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role_names = models.JSONField(default=list)  # List of role names to assign

    # Metadata
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )
    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'invitations'
        verbose_name = 'Invitation'
        verbose_name_plural = 'Invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation for {self.email}"

    def save(self, *args, **kwargs):
        """Set expiration date on create."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=72)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if invitation has expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if invitation is valid for acceptance."""
        return (
            self.status == InvitationStatus.PENDING and
            not self.is_expired
        )

    def mark_accepted(self):
        """Mark invitation as accepted."""
        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

    def mark_cancelled(self):
        """Mark invitation as cancelled."""
        self.status = InvitationStatus.CANCELLED
        self.save()

    def mark_expired(self):
        """Mark invitation as expired."""
        self.status = InvitationStatus.EXPIRED
        self.save()


class InvitationEmailLog(models.Model):
    """
    Log of invitation emails sent.

    Tracks when invitation emails were sent for audit purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(
        Invitation,
        on_delete=models.CASCADE,
        related_name='email_logs'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_to = models.EmailField()
    status = models.CharField(max_length=20)  # 'sent', 'failed', 'bounced'
    error_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'invitation_email_logs'
        verbose_name = 'Invitation Email Log'
        verbose_name_plural = 'Invitation Email Logs'
        ordering = ['-sent_at']

    def __str__(self):
        return f"Email log for {self.invitation.email}"
