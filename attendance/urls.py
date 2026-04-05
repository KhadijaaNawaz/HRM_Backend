"""
Attendance URLs.

Handles attendance tracking endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AttendanceViewSet, AttendanceSettingsView

router = DefaultRouter()
router.register('', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
    path('settings/', AttendanceSettingsView.as_view(), name='attendance-settings'),
]
