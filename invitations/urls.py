"""
Invitation URLs.

Handles invitation management endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import InvitationViewSet, AcceptInvitationView

router = DefaultRouter()
router.register('', InvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
    path('accept/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('resend/', InvitationViewSet.as_view({'post': 'resend_by_email'}), name='resend-invitation'),
]
