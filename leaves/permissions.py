"""
Permission classes for leave management.

Provides role-based access control for leave operations.
"""

from rest_framework import permissions

from accounts.permissions import IsTenantAdmin, IsHROrAdmin


class IsOwnerOrHROrAdmin(permissions.BasePermission):
    """
    Permission class for leave operations.

    - Employees can only access their own leaves
    - HR and Admin can access all leaves
    """

    def has_object_permission(self, request, view, obj):
        """Check permission for a specific leave object."""
        # HR/Admin can access all leaves
        if request.user.is_tenant_admin:
            return True

        # Check if user has HR role
        if request.user.roles.filter(name__in=['HR', 'HR Manager']).exists():
            return True

        # Employees can only access their own leaves
        return obj.employee == request.user

    def has_permission(self, request, view):
        """Check permission for list/create actions."""
        # HR/Admin can access all
        if request.user.is_tenant_admin:
            return True

        # Check if user has HR role
        if request.user.roles.filter(name__in=['HR', 'HR Manager']).exists():
            return True

        # Employees can create and view their own leaves
        # (handled by filtering in get_queryset)
        return True


class CanApproveLeave(permissions.BasePermission):
    """
    Permission class for approving/rejecting leaves.

    Only HR and Admin users can approve or reject leaves.
    """

    def has_permission(self, request, view):
        """Check if user can approve leaves."""
        # Only HR/Admin can approve/reject leaves
        if request.user.is_tenant_admin:
            return True

        # Check if user has HR role
        return request.user.roles.filter(name__in=['HR', 'HR Manager']).exists()


class IsLeaveOwner(permissions.BasePermission):
    """
    Permission class for cancelling own leave requests.

    Employees can only cancel their own pending/approved leaves.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user can cancel this leave."""
        # HR/Admin can cancel any leave
        if request.user.is_tenant_admin:
            return True

        # Employees can only cancel their own leaves
        if obj.employee != request.user:
            return False

        # Can only cancel pending or approved leaves
        return obj.status in [LeaveStatus.PENDING, LeaveStatus.APPROVED]
