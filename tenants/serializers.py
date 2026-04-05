"""
Serializers for tenant models.
"""

from rest_framework import serializers
from django_tenants.utils import schema_context
from .models import Organization, Domain


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain model."""

    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary', 'tenant']
        read_only_fields = ['id']


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'schema_name', 'status',
            'timezone', 'workdays', 'monthly_required_days',
            'public_signup_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'schema_name', 'created_at', 'updated_at']


class OrganizationDetailSerializer(OrganizationSerializer):
    """Detailed serializer for Organization with domains."""
    domains = DomainSerializer(many=True, read_only=True)

    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ['domains']


class CreateTenantSerializer(serializers.Serializer):
    """
    Serializer for creating a new tenant organization.

    This validates the tenant creation request and creates
    both the organization and domain records.
    """
    organization_name = serializers.CharField(max_length=100)
    subdomain = serializers.RegexField(
        regex=r'^[a-z0-9]+(?:-[a-z0-9]+)*$',
        max_length=100,
        help_text="Subdomain must contain only lowercase letters, numbers and hyphens"
    )
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_subdomain(self, value):
        """Check if subdomain is already taken in public schema."""
        from django_tenants.utils import schema_context

        domain = f"{value}.localhost"

        # Check in public schema where domains are stored
        with schema_context('public'):
            if Domain.objects.filter(domain=domain).exists():
                raise serializers.ValidationError("This subdomain is already taken.")

            # Also check if slug is taken
            from .models import Organization
            if Organization.objects.filter(slug=value).exists():
                raise serializers.ValidationError("This subdomain is already taken.")

        return value


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for updating organization settings."""

    class Meta:
        model = Organization
        fields = [
            'timezone', 'workdays', 'monthly_required_days',
            'public_signup_enabled'
        ]


class OrganizationOverviewSerializer(serializers.Serializer):
    """Serializer for organization overview statistics."""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    roles_count = serializers.IntegerField()
    attendance_today = serializers.DictField()
