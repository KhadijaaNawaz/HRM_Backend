"""
Admin URLs for tenant management.

These endpoints are only accessible to platform superusers.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import TenantAdminViewSet

router = DefaultRouter()
router.register(r'tenants', TenantAdminViewSet, basename='admin-tenant')

urlpatterns = [
    path('', include(router.urls)),
    path('create-tenant/', TenantAdminViewSet.as_view({'post': 'create_tenant'}), name='admin-create-tenant'),
]
