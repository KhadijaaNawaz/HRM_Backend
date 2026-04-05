"""
URL configuration for leave management.

Provides URL routes for leave CRUD operations, approval workflows,
and leave balance management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LeaveViewSet,
    LeaveBalanceViewSet
)

# Create router for leave management
router = DefaultRouter()
router.register(r'', LeaveViewSet, basename='leave')
router.register(r'balances', LeaveBalanceViewSet, basename='leavebalance')

urlpatterns = [
    path('', include(router.urls)),
]
