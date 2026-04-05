"""
Views for authentication, user management, and role management.
"""

import uuid
import base64
from datetime import timedelta

from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import logout
from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets, status, generics, filters
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import User, Role, UserRole
from .serializers import (
    UserSerializer, UserDetailSerializer, CreateUserSerializer,
    UpdateUserSerializer, LoginSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, MeSerializer,
    CreateRoleSerializer, RoleSerializer, AssignRoleSerializer,
    RevokeRoleSerializer, UserRoleSerializer
)
from .permissions import IsHROrAdmin, IsTenantAdmin
from .filters import UserFilter, RoleFilter
from django_tenants.utils import get_tenant


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

from audit_logs.models import AuditLog


class PasswordResetThrottle(AnonRateThrottle):
    """Rate limiter for password reset (5/hour)."""
    rate = '5/hour'


class LoginView(TokenObtainPairView):
    """
    Custom login view with tenant validation.

    Handles JWT token generation and returns user info with roles.
    Also logs the login attempt to audit logs.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]  # Allow anyone to login
    authentication_classes = []
    def post(self, request, *args, **kwargs):
        """Process login request."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Check if tenant is active
        from django_tenants.utils import get_tenant
        from django_tenants.middleware.main import TenantMainMiddleware
        tenant = get_tenant(request)
        if tenant and hasattr(tenant, 'status') and tenant.status != 'active':
            return Response(
                {'error': 'Tenant account is suspended.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        # Log login to audit (only if audit_logs tables exist in current schema)
        try:
            from audit_logs.models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='user.login',
                target_model='User',
                target_id=str(user.id),
                ip_address=self.get_client_ip(request),
                meta={'user_agent': request.META.get('HTTP_USER_AGENT', '')}
            )
        except:
            pass  # Audit logs not available in this schema

        # Update last login
        user.last_login = timezone.now()
        user.save()

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': MeSerializer(user).data
        })

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    Logout view that optionally blacklists the refresh token.

    Accepts refresh token in request body and blacklists it if token blacklist is enabled.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout user by optionally blacklisting refresh token."""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                # Try to blacklist if token blacklist app is enabled
                try:
                    token.blacklist()
                except AttributeError:
                    # Blacklist not enabled, token will expire naturally
                    pass

            # Log logout (only if audit_logs tables exist)
            try:
                from audit_logs.models import AuditLog
                AuditLog.objects.create(
                    user=request.user,
                    action='user.logout',
                    target_model='User',
                    target_id=str(request.user.id),
                    ip_address=self.get_client_ip(request)
                )
            except:
                pass  # Audit logs not available in this schema

            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RefreshTokenView(TokenRefreshView):
    """Custom token refresh view."""
    permission_classes = [AllowAny]  # Allow token refresh without auth


class MeView(APIView):
    """Get current user information."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user details."""
        return Response(MeSerializer(request.user).data)


class ForgotPasswordView(APIView):
    """
    Request password reset email.

    Always returns success to prevent email enumeration.
    Throttled to 5 requests per hour per IP.
    """
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        """Process password reset request."""
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        redirect_url = serializer.validated_data['redirect_url']

        # Check if user exists
        try:
            user = User.objects.get(email=email)
            # Generate password reset token
            uid = base64.urlsafe_b64encode(str(user.id).encode()).decode()
            token = default_token_generator.make_token(user)

            # TODO: Send email with reset link
            # For now, just log
            print(f"Password reset for {email}: {redirect_url}?uid={uid}&token={token}")

        except User.DoesNotExist:
            # Don't reveal if email exists
            pass

        return Response({
            'message': 'If email exists, password reset link has been sent.'
        })


class ResetPasswordView(APIView):
    """Reset password with token."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Process password reset."""
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            # Decode user ID
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(id=user_id)

            # Verify token
            if default_token_generator.check_token(user, token):
                user.set_password(new_password)
                user.save()

                # Blacklist all tokens for this user
                OutstandingToken.objects.filter(user_id=user.id).delete()

                return Response({
                    'message': 'Password reset successful.'
                })
            else:
                return Response({
                    'error': 'Invalid or expired token.'
                }, status=status.HTTP_400_BAD_REQUEST)

        except (User.DoesNotExist, ValueError):
            return Response({
                'error': 'Invalid reset link.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change password for authenticated user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Process password change."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Blacklist all tokens for this user
        OutstandingToken.objects.filter(user_id=request.user.id).delete()

        # Log password change (only if audit_logs tables exist)
        try:
            from audit_logs.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                action='user.password_changed',
                target_model='User',
                target_id=str(request.user.id),
                ip_address=self.get_client_ip(request)
            )
        except:
            pass  # Audit logs not available in this schema

        return Response({'message': 'Password changed successfully.'})

    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.

    - Employees can only see their own profile
    - HR can see all users and create new users
    - Admins have full access including soft delete

    Filtering:
    - email: Email address (exact match)
    - email_contains: Email address (partial match)
    - first_name, last_name: Name filters
    - name: Search across first and last name
    - is_active: Active status (true/false)
    - is_tenant_admin: Tenant admin status (true/false)
    - role: Role name (exact match)
    - joined_after: Join date after (YYYY-MM-DD)
    - last_login_days: Last login within X days ago
    - never_logged_in: Users who never logged in (true)
    - search: Global search across email, names, phone

    Ordering:
    - ordering: Order by field (email, -email, date_joined, -date_joined, last_login, -last_login)
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['email', 'date_joined', 'last_login', 'first_name', 'last_name']
    ordering = ['-date_joined']

    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user

        # Tenant admins and HR see all users
        if user.is_tenant_admin or user.roles.filter(name__in=['HR', 'HR Manager']).exists():
            return User.objects.filter(is_active=True)

        # Regular users see only themselves
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return CreateUserSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateUserSerializer
        return UserDetailSerializer

    def perform_create(self, serializer):
        """Create user and log to audit."""
        user = serializer.save()

        # Log user creation
        create_audit_log(
            self.request.user, 'user.created', 'User', user.id,
            meta={'created_email': user.email}
        )

    def perform_update(self, serializer):
        """Update user and log to audit."""
        user = serializer.save()

        # Log user update
        create_audit_log(
            self.request.user, 'user.updated', 'User', user.id
        )

    def perform_destroy(self, instance):
        """Soft delete user."""
        instance.is_active = False
        instance.save()

        # Log user deletion
        create_audit_log(
            self.request.user, 'user.deleted', 'User', instance.id
        )

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return 204 instead of 200."""
        super().perform_destroy(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for role management.

    - All authenticated users can view roles
    - Only admins can create/update/delete custom roles
    - System roles cannot be deleted

    Filtering:
    - name: Role name (exact match)
    - name_contains: Role name (partial match)
    - is_system_role: System role flag (true/false)
    - description: Description (partial match)
    - search: Global search across name and description

    Ordering:
    - ordering: Order by field (name, -name, created_at, -created_at)
    """
    queryset = Role.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RoleFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return CreateRoleSerializer
        return RoleSerializer

    def get_permissions(self):
        """Custom permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsTenantAdmin()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        """Prevent deletion of system roles."""
        if instance.is_system_role:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("System roles cannot be deleted.")
        instance.delete()

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        """Assign role to a user."""
        role = self.get_object()
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])

            # Check if user already has this role
            if UserRole.objects.filter(user=user, role=role).exists():
                return Response({
                    'error': 'User already has this role.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Assign role
            UserRole.objects.create(
                user=user,
                role=role,
                assigned_by=request.user
            )

            # Log role assignment
            create_audit_log(
                request.user, 'role.assigned', 'UserRole', f"{user.id}:{role.id}",
                meta={'user_email': user.email, 'role_name': role.name}
            )

            return Response({
                'message': f'Role {role.name} assigned to {user.email}'
            })

        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke(self, request, pk=None):
        """Revoke role from a user."""
        role = self.get_object()
        serializer = RevokeRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = User.objects.get(id=serializer.validated_data['user_id'])

            # Check if user has this role
            user_role = UserRole.objects.filter(user=user, role=role).first()
            if not user_role:
                return Response({
                    'error': 'User does not have this role.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Revoke role
            user_role.delete()

            # Log role revocation
            create_audit_log(
                request.user, 'role.revoked', 'UserRole', f"{user.id}:{role.id}",
                meta={'user_email': user.email, 'role_name': role.name}
            )

            return Response({
                'message': f'Role {role.name} revoked from {user.email}'
            })

        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)


class CurrentUserDetailView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user's profile.
    """
    serializer_class = UpdateUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return current user."""
        return self.request.user

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.request.method == 'GET':
            return MeSerializer
        return UpdateUserSerializer
