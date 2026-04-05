"""
Custom tenant middleware that supports both Host header and x-tenant-id header.

This allows more flexible tenant resolution:
1. Via Host header: acme.localhost
2. Via custom header: x-tenant-id: acme
3. Via query parameter: ?tenant=acme
"""

from django_tenants.middleware.main import TenantMainMiddleware
from django.http import Http404
from django.db import connection
from tenants.models import Domain


class FlexibleTenantMiddleware:
    """
    Enhanced tenant middleware with multiple tenant resolution methods.

    Priority order:
    1. x-tenant-id header (custom header)
    2. Host header (subdomain)
    3. tenant query parameter
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.public_schema_name = 'public'

    def __call__(self, request):
        # Try to get tenant from various sources
        tenant = self.get_tenant_from_request(request)

        if tenant is None:
            # No tenant found, return 404 or serve public schema
            return self.handle_no_tenant(request)

        # Set tenant for this request
        request.tenant = tenant
        connection.set_schema(tenant.schema_name)

        response = self.get_response(request)

        return response

    def get_tenant_from_request(self, request):
        """
        Try to get tenant from multiple sources in priority order.
        """
        # Method 1: Custom header (highest priority)
        tenant_from_header = self.get_tenant_from_header(request)
        if tenant_from_header:
            return tenant_from_header

        # Method 2: Host header (subdomain-based)
        tenant_from_host = self.get_tenant_from_host(request)
        if tenant_from_host:
            return tenant_from_host

        # Method 3: Query parameter (fallback)
        tenant_from_param = self.get_tenant_from_query_param(request)
        if tenant_from_param:
            return tenant_from_param

        return None

    def get_tenant_from_header(self, request):
        """
        Get tenant from x-tenant-id or X-Host header.

        Examples:
            x-tenant-id: acme
            x-tenant-id: techcorp
            X-Host: acme.localhost
            X-Host: acme.yourapp.com
        """
        # Try x-tenant-id header first (tenant slug)
        tenant_id = request.headers.get('x-tenant-id') or request.headers.get('X-Tenant-Id')

        # If not found, try X-Host header (full hostname)
        if not tenant_id:
            host_header = request.headers.get('X-Host') or request.headers.get('x-host')
            if host_header:
                # Extract subdomain from hostname (e.g., "acme.localhost" -> "acme")
                # If hostname has no subdomain (e.g., "localhost"), return None
                parts = host_header.split('.')
                # Check if we have a subdomain (more than 2 parts, or 2 parts where first isn't "localhost")
                if len(parts) >= 2 and parts[0] != 'localhost' and parts[0] != '127-0-0-1':
                    # Has subdomain: acme.localhost or acme.yourapp.com
                    tenant_id = parts[0]

        if not tenant_id:
            return None

        try:
            # Try to find by slug
            from tenants.models import Organization
            try:
                return Organization.objects.get(slug=tenant_id, schema_name=tenant_id.replace('-', '_'))
            except Organization.DoesNotExist:
                pass

            # Try to find by domain
            try:
                domain = Domain.objects.select_related('tenant').get(domain=tenant_id)
                return domain.tenant
            except Domain.DoesNotExist:
                pass

            # Try to find by ID
            try:
                return Organization.objects.get(id=tenant_id)
            except (Organization.DoesNotExist, ValidationError):
                pass

        except Exception as e:
            # Log error but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get tenant from x-tenant-id header: {e}")

        return None

    def get_tenant_from_host(self, request):
        """
        Get tenant from Host header (original django-tenants behavior).
        """
        host = request.get_host().split(':')[0]  # Remove port if present

        try:
            domain = Domain.objects.select_related('tenant').get(domain=host)
            return domain.tenant
        except Domain.DoesNotExist:
            return None

    def get_tenant_from_query_param(self, request):
        """
        Get tenant from tenant query parameter.

        Example: /api/v1/auth/login/?tenant=acme
        """
        tenant_id = request.GET.get('tenant')

        if not tenant_id:
            return None

        try:
            # Try to find by slug first
            from tenants.models import Organization
            try:
                return Organization.objects.get(slug=tenant_id)
            except Organization.DoesNotExist:
                pass

            # Try to find by ID
            try:
                return Organization.objects.get(id=tenant_id)
            except (Organization.DoesNotExist, ValidationError):
                pass

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to get tenant from tenant param: {e}")

        return None

    def handle_no_tenant(self, request):
        """
        Handle requests where no tenant could be determined.
        """
        # Allow OPTIONS preflight requests without tenant (CORS)
        if request.method == 'OPTIONS':
            connection.set_schema(self.public_schema_name)
            return self.get_response(request)

        # For public endpoints, serve from public schema
        # Auth endpoints are public (login, refresh, forgot-password, reset-password)
        public_paths = [
            '/health/',
            '/api/health/',
            '/api/v1/public/',
            '/api/v1/auth/login/',
            '/api/v1/auth/refresh/',
            '/api/v1/auth/forgot-password/',
            '/api/v1/auth/reset-password/',
        ]

        if any(request.path.startswith(path) for path in public_paths):
            connection.set_schema(self.public_schema_name)
            return self.get_response(request)

        # For API endpoints, return 401 with helpful message
        if request.path.startswith('/api/'):
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'Tenant not specified',
                'message': 'Please provide tenant via x-tenant-id header, X-Host header, or ?tenant= query parameter',
                'examples': [
                    'Header: x-tenant-id: acme',
                    'Header: X-Host: acme.localhost',
                    'URL: /api/v1/auth/login/?tenant=acme'
                ]
            }, status=401)

        # For other paths, serve a 404 or tenant selection page
        from django.http import Http404
        raise Http404('Tenant not found. Please specify a tenant.')


# Backwards compatible alias for existing imports
from django.utils.module_loading import import_string
from django.core.exceptions import ImproperlyConfigured

def get_tenant_middleware():
    """
    Get the tenant middleware class from settings.
    Allows custom middleware while maintaining compatibility.
    """
    from django.conf import settings

    path = getattr(settings, 'TENANT_MIDDLEWARE', None)
    if path:
        try:
            return import_string(path)
        except ImportError as e:
            raise ImproperlyConfigured(f"TENANT_MIDDLEWARE '{path}' could not be imported: {e}")

    # Default to flexible middleware
    return FlexibleTenantMiddleware
