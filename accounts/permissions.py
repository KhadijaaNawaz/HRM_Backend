"""
Custom permission classes for accounts app.

These are re-exported from tenants.permissions for convenience
and to avoid circular imports.
"""

from tenants.permissions import (
    IsSuperUser,
    IsTenantAdmin,
    IsHROrAdmin,
    IsOwnerOrAdmin,
    IsActiveTenant,
    IsHR,
    IsEmployee,
)

__all__ = [
    'IsSuperUser',
    'IsTenantAdmin',
    'IsHROrAdmin',
    'IsOwnerOrAdmin',
    'IsActiveTenant',
    'IsHR',
    'IsEmployee',
]
