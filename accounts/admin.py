"""
Admin configuration for accounts models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Role, UserRole


class UserRoleInline(admin.TabularInline):
    """Inline admin for user roles."""
    model = UserRole
    fk_name = 'user'
    extra = 0
    readonly_fields = ['assigned_at']


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin interface for User model."""
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_tenant_admin', 'date_joined']
    list_filter = ['is_active', 'is_tenant_admin', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['id', 'date_joined', 'updated_at', 'last_login']
    inlines = [UserRoleInline]

    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_tenant_admin', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'updated_at')
        }),
        ('Metadata', {
            'fields': ('id',)
        }),
    )

    add_fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password1', 'password2')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone')
        }),
    )

    ordering = ['-date_joined']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""
    list_display = ['name', 'is_system_role', 'description', 'created_at']
    list_filter = ['is_system_role', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def delete_model(self, request, obj):
        """Prevent deletion of system roles."""
        if obj.is_system_role:
            from django.contrib import messages
            messages.error(request, "System roles cannot be deleted.")
            return
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Prevent deletion of system roles in bulk actions."""
        queryset = queryset.filter(is_system_role=False)
        super().delete_queryset(request, queryset)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin interface for UserRole model."""
    list_display = ['user', 'role', 'assigned_at', 'assigned_by']
    list_filter = ['role', 'assigned_at']
    search_fields = ['user__email', 'role__name']
    readonly_fields = ['assigned_at']
