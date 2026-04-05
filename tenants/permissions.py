"""
Custom permission classes for HRM SaaS.

This module provides permission classes for role-based access control
and tenant-specific permissions.

Role Hierarchy (4 tiers):
1. Superuser (is_superuser=True) - Platform-level admin, manages all tenants
2. Admin (tenant admin) - Full access within tenant organization
3. HR - User and attendance management within tenant
4. Employee - Self-service (own attendance and profile)
"""

from rest_framework import permissions
from django_tenants.utils import get_tenant


class IsSuperUser(permissions.BasePermission):
    """
    Permission class for platform superusers only.

    Superusers can manage all tenants and have unrestricted access.
    This is Django's built-in is_superuser flag.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


class IsTenantAdmin(permissions.BasePermission):
    """
    Permission class for tenant administrators.

    Tenant admins have full access within their tenant's scope.
    This is the is_tenant_admin flag on the User model.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'is_tenant_admin', False)
        )


class IsHR(permissions.BasePermission):
    """
    Permission class for HR users.

    HR users can:
    - Manage users (create, update, view)
    - Manage attendance for all users
    - Send invitations
    - View attendance reports

    But cannot:
    - Modify organization settings
    - Manage roles
    - Access audit logs
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Tenant admins and superusers have all HR permissions
        if getattr(request.user, 'is_tenant_admin', False) or request.user.is_superuser:
            return True

        # Check if user has HR role
        return request.user.roles.filter(name='HR').exists()


class IsEmployee(permissions.BasePermission):
    """
    Permission class for employees.

    Employees can:
    - Check in/out
    - View own attendance
    - Update own profile
    - View own roles
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # All authenticated users (including HR, Admin, Superuser) are employees
        return True


class IsHROrAdmin(permissions.BasePermission):
    """
    Permission class for HR users or tenant administrators.

    HR users and tenant admins can:
    - View all users
    - Create and manage users
    - View all attendance records
    - Send invitations
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Tenant admins and superusers have all access
        if getattr(request.user, 'is_tenant_admin', False) or request.user.is_superuser:
            return True

        # Check if user has HR role
        return request.user.roles.filter(name='HR').exists()


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to resource owners or admins.

    For user-specific resources like attendance records and profiles.
    - Superusers: Full access
    - Tenant Admins: Full access within tenant
    - HR: Full access within tenant
    - Employees: Access to own resources only
    """
    def has_object_permission(self, request, view, obj):
        # Superusers can access any object
        if request.user.is_superuser:
            return True

        # Tenant admins can access any object within tenant
        if getattr(request.user, 'is_tenant_admin', False):
            return True

        # HR can access any object within tenant
        if request.user.roles.filter(name='HR').exists():
            return True

        # Check if the user owns the object
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if the object is the user themselves
        if obj == request.user:
            return True

        return False


class IsActiveTenant(permissions.BasePermission):
    """
    Permission class to ensure the tenant is active.

    Suspended tenants cannot access the API.
    """
    def has_permission(self, request, view):
        tenant = get_tenant(request)
        if not tenant:
            return False

        # Check if tenant has status attribute (Organization model)
        if hasattr(tenant, 'status'):
            return tenant.status == 'active'
        return True
