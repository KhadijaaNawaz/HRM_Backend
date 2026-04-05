"""
Tenant models for HRM SaaS multi-tenancy.

This module contains the Organization (Tenant) and Domain models
that enable schema-based tenant isolation using django-tenants.
"""

from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import uuid


class OrganizationStatus(models.TextChoices):
    """Organization status choices."""
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'
    PENDING = 'pending', 'Pending'


class Organization(TenantMixin):
    """
    Tenant model representing an organization in the HRM SaaS system.

    Each organization gets its own PostgreSQL schema for complete data isolation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.PENDING
    )

    # Organization settings
    timezone = models.CharField(max_length=50, default='UTC')
    workdays = models.JSONField(default=list)  # ['mon', 'tue', 'wed', 'thu', 'fri']
    monthly_required_days = models.IntegerField(default=22)
    public_signup_enabled = models.BooleanField(default=False)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # django-tenants configuration
    auto_create_schema = True
    auto_drop_schema = False

    class Meta:
        db_table = 'organizations'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Set default workdays if not provided
        if not self.workdays:
            self.workdays = ['mon', 'tue', 'wed', 'thu', 'fri']

        # Generate schema_name from slug if not set
        if not self.schema_name:
            self.schema_name = self.slug.replace('-', '_')

        super().save(*args, **kwargs)


class Domain(DomainMixin):
    """
    Domain model for mapping domains/subdomains to organizations.

    Example: acme.localhost maps to the 'acme' organization.
    """
    class Meta:
        db_table = 'domains'
        verbose_name = 'Domain'
        verbose_name_plural = 'Domains'

    def __str__(self):
        return self.domain
