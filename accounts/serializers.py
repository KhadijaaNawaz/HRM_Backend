"""
Serializers for accounts models.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Role, UserRole


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'is_system_role', 'created_at', 'updated_at']
        read_only_fields = ['id', 'is_system_role', 'created_at', 'updated_at']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model."""
    role = RoleSerializer(read_only=True)
    role_id = serializers.UUIDField(write_only=True)
    assigned_by_email = serializers.EmailField(source='assigned_by.email', read_only=True)

    class Meta:
        model = UserRole
        fields = ['id', 'role', 'role_id', 'assigned_at', 'assigned_by_email']
        read_only_fields = ['id', 'assigned_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    roles = RoleSerializer(many=True, read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'is_active', 'is_tenant_admin', 'profile_picture',
            'date_joined', 'last_login', 'roles'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login'
        ]


class UserDetailSerializer(UserSerializer):
    """Detailed serializer for User with user roles."""
    user_roles = UserRoleSerializer(
        many=True,
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['user_roles']


class CreateUserSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    role_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of role names to assign (e.g., ['Employee', 'HR Manager'])"
    )

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name',
            'phone', 'role_names'
        ]

    def create(self, validated_data):
        """Create user and assign roles."""
        role_names = validated_data.pop('role_names', [])
        user = User.objects.create_user(**validated_data)

        # Assign roles if provided
        if role_names:
            for role_name in role_names:
                try:
                    role = Role.objects.get(name=role_name)
                    UserRole.objects.create(user=user, role=role)
                except Role.DoesNotExist:
                    pass  # Skip invalid roles

        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'profile_picture'
        ]


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Validate credentials and return user if valid."""
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    'This user account has been disabled.',
                    code='authorization'
                )

            attrs['user'] = user
            return attrs

        raise serializers.ValidationError(
            'Must include "email" and "password".',
            code='authorization'
        )


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Old password is incorrect.'
            )
        return value

    def save(self):
        """Change user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for password reset request."""
    email = serializers.EmailField()
    redirect_url = serializers.URLField()

    def validate_email(self, value):
        """Always return success to prevent email enumeration."""
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset with token."""
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        validators=[validate_password],
        write_only=True,
        style={'input_type': 'password'}
    )


class MeSerializer(serializers.ModelSerializer):
    """Serializer for current user info."""
    roles = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone',
            'is_active', 'is_tenant_admin', 'is_superuser', 'roles', 'organization'
        ]

    def get_roles(self, obj):
        """Get user's roles."""
        try:
            return RoleSerializer(obj.roles.all(), many=True).data
        except:
            return []  # Return empty list if roles can't be fetched

    def get_organization(self, obj):
        """Get organization info."""
        try:
            from django_tenants.utils import get_tenant
            # Get current request from context
            request = self.context.get('request')
            if request:
                tenant = get_tenant(request)
                if tenant:
                    return {
                        'id': str(tenant.id),
                        'name': tenant.name,
                        'slug': tenant.slug,
                        'status': tenant.status if hasattr(tenant, 'status') else 'active'
                    }
        except:
            pass
        return None


class CreateRoleSerializer(serializers.ModelSerializer):
    """Serializer for creating custom roles."""

    class Meta:
        model = Role
        fields = ['name', 'description']

    def validate_name(self, value):
        """Prevent creating system roles."""
        system_roles = ['Admin', 'HR', 'HR Manager', 'Employee']
        if value in system_roles:
            raise serializers.ValidationError(
                f'Cannot create system role "{value}".'
            )
        return value


class AssignRoleSerializer(serializers.Serializer):
    """Serializer for assigning role to user."""
    user_id = serializers.UUIDField()


class RevokeRoleSerializer(serializers.Serializer):
    """Serializer for revoking role from user."""
    user_id = serializers.UUIDField()
