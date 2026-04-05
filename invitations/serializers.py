"""
Serializers for invitation models.
"""

from rest_framework import serializers
from django.utils import timezone
from .models import Invitation, InvitationStatus


class InvitationSerializer(serializers.ModelSerializer):
    """Serializer for Invitation model."""
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invitation
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role_names',
            'status', 'invited_by', 'invited_by_email',
            'created_at', 'updated_at', 'expires_at', 'accepted_at',
            'is_expired', 'is_valid'
        ]
        read_only_fields = [
            'id', 'token', 'status', 'invited_by',
            'created_at', 'updated_at', 'expires_at', 'accepted_at'
        ]


class CreateInvitationSerializer(serializers.ModelSerializer):
    """Serializer for creating new invitations."""
    role_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['Employee']
    )

    class Meta:
        model = Invitation
        fields = ['email', 'first_name', 'last_name', 'role_names']

    def validate_email(self, value):
        """Check if user with this email already exists."""
        from accounts.models import User
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'A user with this email already exists.'
            )
        return value

    def validate_role_names(self, value):
        """Validate that roles exist."""
        from accounts.models import Role
        valid_roles = Role.objects.filter(name__in=value).values_list('name', flat=True)
        invalid_roles = set(value) - set(valid_roles)
        if invalid_roles:
            raise serializers.ValidationError(
                f'Invalid roles: {", ".join(invalid_roles)}'
            )
        return value

    def create(self, validated_data):
        """Create invitation and send email."""
        # Extract invited_by from context
        invited_by = self.context['request'].user

        # Create invitation
        invitation = Invitation.objects.create(
            invited_by=invited_by,
            **validated_data
        )

        # TODO: Send invitation email
        # For now, just log it
        print(f"Invitation token for {invitation.email}: {invitation.token}")

        return invitation


class AcceptInvitationSerializer(serializers.Serializer):
    """Serializer for accepting invitations."""
    token = serializers.UUIDField()
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_token(self, value):
        """Validate token exists and is valid."""
        try:
            invitation = Invitation.objects.get(token=value)
            if not invitation.is_valid:
                if invitation.is_expired:
                    raise serializers.ValidationError(
                        'This invitation has expired.'
                    )
                raise serializers.ValidationError(
                    'This invitation is no longer valid.'
                )
            self.invitation = invitation
        except Invitation.DoesNotExist:
            raise serializers.ValidationError(
                'Invalid invitation token.'
            )
        return value


class ResendInvitationSerializer(serializers.Serializer):
    """Serializer for resending invitations."""
    email = serializers.EmailField(required=False)
    invite_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        """Validate either email or invite_id is provided."""
        if not attrs.get('email') and not attrs.get('invite_id'):
            raise serializers.ValidationError(
                'Either email or invite_id must be provided.'
            )
        return attrs


class InvitationDetailSerializer(InvitationSerializer):
    """Detailed serializer for single invitation."""
    token = serializers.UUIDField(read_only=True)
