"""
Organization URLs for tenant-specific settings and overview.
"""

from django.urls import path
from ..views import OrganizationOverviewView, OrganizationSettingsView

urlpatterns = [
    path('overview/', OrganizationOverviewView.as_view(), name='org-overview'),
    path('settings/', OrganizationSettingsView.as_view(), name='org-settings'),
]
