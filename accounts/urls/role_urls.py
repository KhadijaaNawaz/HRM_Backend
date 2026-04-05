"""
Role management URLs.

Handles role CRUD, assign, and revoke operations.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import RoleViewSet

router = DefaultRouter()
router.register('', RoleViewSet, basename='role')

urlpatterns = [
    path('', include(router.urls)),
]
