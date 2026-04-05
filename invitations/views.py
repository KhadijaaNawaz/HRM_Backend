"""
Views for invitation management.

Handles creating, accepting, cancelling, and resending invitations.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend

from .models import Invitation, InvitationStatus
from .serializers import (
    InvitationSerializer,
    InvitationDetailSerializer,
    CreateInvitationSerializer,
    AcceptInvitationSerializer,
    ResendInvitationSerializer
)
from .filters import InvitationFilter
from accounts.permissions import IsHROrAdmin
from accounts.models import User, Role


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


class InvitationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for invitation management.

    - HR/Admin can create and view invitations
    - Only creator can cancel their invitations
    - Public endpoint for accepting invitations

    Filtering:
    - email: Email address (exact match)
    - email_contains: Email address (partial match)
    - status: Invitation status (pending, accepted, cancelled, expired)
    - first_name, last_name: Name filters
    - invited_by: Invited by user ID (UUID)
    - invited_by_email: Invited by user email (partial match)
    - created_after: Creation date after (YYYY-MM-DD)
    - is_expired: Filter expired invitations (true)
    - is_valid: Filter valid invitations (true)
    - search: Global search across email and names

    Ordering:
    - ordering: Order by field (created_at, -created_at, expires_at, -expires_at)
    """
    permission_classes = [IsAuthenticated, IsHROrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InvitationFilter
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'expires_at', 'accepted_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return invitations for current tenant."""
        return Invitation.objects.all().select_related('invited_by')

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return CreateInvitationSerializer
        elif self.action == 'retrieve':
            return InvitationDetailSerializer
        return InvitationSerializer

    def perform_create(self, serializer):
        """Create invitation with current user as inviter."""
        invitation = serializer.save()

        # Log invitation creation
        create_audit_log(
            self.request.user, 'invite.created', 'Invitation', invitation.id,
            meta={
                'email': invitation.email,
                'role_names': invitation.role_names
            }
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Cancel a pending invitation."""
        invitation = self.get_object()

        if invitation.status != InvitationStatus.PENDING:
            return Response({
                'error': 'Only pending invitations can be cancelled.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user created this invitation
        if invitation.invited_by != request.user and not request.user.is_tenant_admin:
            return Response({
                'error': 'You can only cancel your own invitations.'
            }, status=status.HTTP_403_FORBIDDEN)

        invitation.mark_cancelled()

        # Log cancellation
        create_audit_log(
            request.user, 'invite.cancelled', 'Invitation', invitation.id,
            meta={'email': invitation.email}
        )

        return Response({'message': 'Invitation cancelled successfully.'})

    @action(detail=True, methods=['post'], url_path='resend')
    def resend(self, request, pk=None):
        """Resend an invitation email."""
        invitation = self.get_object()

        if invitation.status != InvitationStatus.PENDING:
            return Response({
                'error': 'Only pending invitations can be resent.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Resend email
        print(f"Resending invitation token for {invitation.email}: {invitation.token}")

        # Log resend
        create_audit_log(
            request.user, 'invite.resent', 'Invitation', invitation.id,
            meta={'email': invitation.email}
        )

        return Response({'message': 'Invitation email resent successfully.'})

    @action(detail=False, methods=['post'], url_path='resend')
    def resend_by_email(self, request):
        """Resend invitation by email address."""
        serializer = ResendInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Find invitation
        invitation = None
        if serializer.validated_data.get('invite_id'):
            invitation = Invitation.objects.filter(
                id=serializer.validated_data['invite_id']
            ).first()
        elif serializer.validated_data.get('email'):
            invitation = Invitation.objects.filter(
                email=serializer.validated_data['email'],
                status=InvitationStatus.PENDING
            ).first()

        if not invitation:
            return Response({
                'error': 'No pending invitation found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # TODO: Resend email
        print(f"Resending invitation token for {invitation.email}: {invitation.token}")

        # Log resend
        create_audit_log(
            request.user, 'invite.resent', 'Invitation', invitation.id,
            meta={'email': invitation.email}
        )

        return Response({'message': 'Invitation email resent successfully.'})


class AcceptInvitationView(APIView):
    """
    Public endpoint for accepting invitations.

    Validates the invitation token and creates a new user account.
    Returns JWT tokens on successful acceptance.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Accept invitation and create user."""
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation = serializer.invitation
        password = serializer.validated_data['password']

        # Create user account
        user = User.objects.create_user(
            email=invitation.email,
            password=password,
            first_name=invitation.first_name,
            last_name=invitation.last_name
        )

        # Assign roles
        for role_name in invitation.role_names:
            try:
                role = Role.objects.get(name=role_name)
                from accounts.models import UserRole
                UserRole.objects.create(user=user, role=role)
            except Role.DoesNotExist:
                pass  # Skip invalid roles

        # Mark invitation as accepted
        invitation.mark_accepted()

        # Log invitation acceptance
        create_audit_log(
            user, 'invite.accepted', 'Invitation', invitation.id,
            meta={'invitation_email': invitation.email}
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }, status=status.HTTP_201_CREATED)
