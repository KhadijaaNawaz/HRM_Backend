"""
URL configuration for notification system.

Provides URL routes for notification retrieval, read/unread actions,
and notification statistics.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet

# Create router for notifications
router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
