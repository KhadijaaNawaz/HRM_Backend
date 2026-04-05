"""
Admin configuration for tenant models.
"""

from django.contrib import admin
from .models import Organization, Domain


class DomainInline(admin.TabularInline):
    """Inline admin for domains within organization."""
    model = Domain
    extra = 0
    fields = ('domain', 'is_primary')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organization model."""
    list_display = ['name', 'slug', 'schema_name', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'slug', 'schema_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'schema_name']
    inlines = [DomainInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'status', 'schema_name')
        }),
        ('Organization Settings', {
            'fields': ('timezone', 'workdays', 'monthly_required_days', 'public_signup_enabled')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin interface for Domain model."""
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain']
