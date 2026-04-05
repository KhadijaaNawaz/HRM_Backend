"""
Authentication URLs.

Handles login, logout, token refresh, password management,
and current user info.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from ..views import (
    LoginView,
    LogoutView,
    MeView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('password/forgot/', ForgotPasswordView.as_view(), name='password_forgot'),
    path('password/reset/', ResetPasswordView.as_view(), name='password_reset'),
    path('password/change/', ChangePasswordView.as_view(), name='password_change'),
]
