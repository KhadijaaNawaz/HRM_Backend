"""
URL configuration for HRM SaaS project.

Multi-tenant HRM SaaS API with JWT authentication.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    # path('admin/', admin.site.urls),  # Temporarily disabled - will add back after tenant setup

    # API v1 Endpoints
    path('api/v1/admin/', include('tenants.urls.admin_urls')),    # Superuser only
    path('api/v1/auth/', include('accounts.urls.auth_urls')),      # Authentication
    path('api/v1/users/', include('accounts.urls.user_urls')),     # User management
    path('api/v1/roles/', include('accounts.urls.role_urls')),     # Role management
    path('api/v1/invite/', include('invitations.urls')),           # Invitations
    path('api/v1/attendance/', include('attendance.urls')),        # Attendance
    path('api/v1/organization/', include('tenants.urls.org_urls')),# Organization settings
    path('api/v1/audit/', include('audit_logs.urls')),  # Audit logs
    path('api/v1/leaves/', include('leaves.urls')),      # Leave management
    path('api/v1/notifications/', include('notifications.urls')),  # Notifications
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
