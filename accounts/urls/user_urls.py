"""
User management URLs.

Handles user CRUD operations and current user profile.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import UserViewSet, CurrentUserDetailView

router = DefaultRouter()
router.register('', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', CurrentUserDetailView.as_view(), name='current-user-detail'),
]
