"""
Views for tenant management and organization settings.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django_filters.rest_framework import DjangoFilterBackend
from django_tenants.utils import schema_context, tenant_context

from .models import Organization, Domain
from .serializers import (
    OrganizationSerializer,
    OrganizationDetailSerializer,
    CreateTenantSerializer,
    OrganizationSettingsSerializer,
    OrganizationOverviewSerializer
)
from .permissions import IsSuperUser, IsTenantAdmin, IsHROrAdmin
from .filters import OrganizationFilter


class TenantAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants (organizations).

    Only accessible to platform superusers.
    Provides CRUD operations on organizations/tenants.

    Filtering:
    - name: Organization name (exact match)
    - name_contains: Organization name (partial match)
    - slug: Organization slug (exact match)
    - status: Organization status (active, suspended, pending)
    - timezone: Timezone (exact match)
    - public_signup_enabled: Public signup flag (true/false)
    - created_days: Created within X days ago
    - search: Global search across name and slug

    Ordering:
    - ordering: Order by field (name, -name, created_at, -created_at)
    """
    serializer_class = OrganizationDetailSerializer
    queryset = Organization.objects.all().order_by('-created_at')
    permission_classes = [IsSuperUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OrganizationFilter
    search_fields = ['name', 'slug']
    ordering_fields = ['name', 'created_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return CreateTenantSerializer
        return OrganizationDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new tenant organization with admin user.

        This overrides the default create method to:
        1. Create the Organization (tenant) in public schema
        2. Create the Domain record
        3. Create admin user in the new tenant schema
        4. Create default roles
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Use public schema context for tenant creation
        with schema_context('public'):
            try:
                # Check if subdomain is already taken
                subdomain = data['subdomain']
                domain_name = f"{subdomain}.localhost"

                if Domain.objects.filter(domain=domain_name).exists():
                    return Response({
                        'error': f"Subdomain '{subdomain}' is already taken."
                    }, status=status.HTTP_400_BAD_REQUEST)

                if Organization.objects.filter(slug=subdomain).exists():
                    return Response({
                        'error': f"Organization slug '{subdomain}' is already taken."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create Organization
                org = Organization.objects.create(
                    name=data['organization_name'],
                    slug=subdomain,
                    status='active'
                )

                # Create Domain
                Domain.objects.create(
                    domain=domain_name,
                    tenant=org,
                    is_primary=True
                )

                # Create admin user in the new tenant schema
                with tenant_context(org):
                    from accounts.models import User, Role, UserRole

                    # Create default roles
                    for role_name, role_desc in [
                        ('Admin', 'Tenant administrator'),
                        ('HR', 'HR Manager'),
                        ('HR Manager', 'Senior HR Manager'),
                        ('Employee', 'Regular employee')
                    ]:
                        Role.objects.get_or_create(
                            name=role_name,
                            defaults={'description': role_desc, 'is_system_role': True}
                        )

                    # Create admin user
                    admin = User.objects.create_superuser(
                        email=data['email'],
                        password=data['password'],
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        phone=data.get('phone', '')
                    )
                    admin.is_tenant_admin = True
                    admin.save()

                    # Assign Admin role
                    admin_role = Role.objects.get(name='Admin')
                    UserRole.objects.create(user=admin, role=admin_role)

                # Return the created organization
                serializer = OrganizationDetailSerializer(org)
                headers = self.get_success_headers(serializer.data)
                return Response({
                    'organization': serializer.data,
                    'admin_email': data['email'],
                    'message': 'Tenant created successfully with admin user.'
                }, status=status.HTTP_201_CREATED, headers=headers)

            except Exception as e:
                # Cleanup on error
                if 'org' in locals():
                    try:
                        org.delete(force_drop=True)
                    except:
                        pass
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

    # Deprecated: Use POST /tenants/ instead
    def create_tenant(self, request):
        """
        Create a new tenant organization with admin user.

        This endpoint:
        1. Creates the Organization (tenant) in public schema
        2. Creates the Domain record
        3. Runs migrations for the new schema
        4. Creates admin user in the new tenant schema
        5. Creates default roles
        6. Returns JWT tokens for the new admin

        Request body:
        {
            "organization_name": "Acme Corporation",
            "subdomain": "acme",
            "email": "admin@acme.com",
            "password": "TenantAdmin123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890"
        }
        """
        serializer = CreateTenantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Use public schema context for tenant creation
        with schema_context('public'):
            try:
                # Check if subdomain is already taken
                domain_name = f"{data['subdomain']}.localhost"
                if Domain.objects.filter(domain=domain_name).exists():
                    return Response({
                        'error': f"Subdomain '{data['subdomain']}' is already taken."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if slug is already taken
                if Organization.objects.filter(slug=data['subdomain']).exists():
                    return Response({
                        'error': f"Organization slug '{data['subdomain']}' is already taken."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create Organization in public schema
                org = Organization.objects.create(
                    name=data['organization_name'],
                    slug=data['subdomain'],
                    status='active'
                )

                # Create Domain record
                domain = Domain.objects.create(
                    domain=domain_name,
                    tenant=org,
                    is_primary=True
                )

                # Create admin user in the new tenant schema
                with tenant_context(org):
                    from accounts.models import User, Role, UserRole

                    # Create default roles
                    for role_name, role_desc in [
                        ('Admin', 'Tenant administrator'),
                        ('HR', 'HR Manager'),
                        ('HR Manager', 'Senior HR Manager'),
                        ('Employee', 'Regular employee')
                    ]:
                        Role.objects.get_or_create(
                            name=role_name,
                            defaults={'description': role_desc, 'is_system_role': True}
                        )

                    # Create admin user
                    admin = User.objects.create_superuser(
                        email=data['email'],
                        password=data['password'],
                        first_name=data['first_name'],
                        last_name=data['last_name'],
                        phone=data.get('phone', '')
                    )
                    admin.is_tenant_admin = True
                    admin.save()

                    # Assign Admin role
                    admin_role = Role.objects.get(name='Admin')
                    UserRole.objects.create(user=admin, role=admin_role)

                return Response({
                    'organization': OrganizationDetailSerializer(org).data,
                    'admin_email': data['email'],
                    'message': 'Tenant created successfully with admin user.'
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                # Cleanup on error
                if 'org' in locals():
                    try:
                        org.delete(force_drop=True)
                    except:
                        pass
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a suspended tenant."""
        org = self.get_object()
        org.status = 'active'
        org.save()
        return Response({'message': 'Tenant activated successfully'})

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend an active tenant."""
        org = self.get_object()
        org.status = 'suspended'
        org.save()
        return Response({'message': 'Tenant suspended successfully'})

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """
        List all users for a specific tenant.

        This endpoint switches to the tenant's schema and retrieves users.
        """
        org = self.get_object()

        # Switch to tenant schema
        with tenant_context(org):
            # Import User model here to avoid circular imports
            from accounts.models import User

            users = User.objects.filter(is_active=True)
            # TODO: Add user serializer and return paginated list
            return Response({
                'tenant': org.name,
                'users_count': users.count()
            })


class OrganizationOverviewView(APIView):
    """
    Get organization-wide statistics and overview.

    Accessible to HR users and tenant admins.
    """
    permission_classes = [IsHROrAdmin]

    def get(self, request):
        """Return organization overview statistics."""
        from accounts.models import User
        from accounts.models import Role
        from attendance.models import Attendance
        from django.utils import timezone
        from datetime import date

        tenant = request.tenant

        # Get statistics
        total_users = User.objects.filter(is_active=True).count()
        active_users = User.objects.filter(
            is_active=True,
            last_login__gte=timezone.now() - timezone.timedelta(days=30)
        ).count()
        roles_count = Role.objects.count()

        # Get today's attendance
        today = date.today()
        attendance_today = Attendance.objects.filter(date=today)
        present_today = attendance_today.filter(checkin_time__isnull=False).count()

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'roles_count': roles_count,
            'attendance_today': {
                'total': attendance_today.count(),
                'present': present_today,
                'pending': attendance_today.count() - present_today
            }
        })


class OrganizationSettingsView(APIView):
    """
    Get and update organization settings.

    Accessible to tenant admins only for updates.
    All authenticated users can view settings.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current organization settings."""
        tenant = request.tenant
        serializer = OrganizationSettingsSerializer(tenant)
        return Response(serializer.data)

    def put(self, request):
        """Update organization settings (admin only)."""
        # Check if user is tenant admin
        if not getattr(request.user, 'is_tenant_admin', False):
            return Response(
                {'error': 'Only tenant admins can update organization settings.'},
                status=status.HTTP_403_FORBIDDEN
            )

        tenant = request.tenant
        serializer = OrganizationSettingsSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
