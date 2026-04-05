"""
Leaves app configuration for HRM SaaS.
"""

from django.apps import AppConfig


class LeavesConfig(AppConfig):
    """Leaves app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leaves'
    verbose_name = 'Leave Management'

    def ready(self):
        """Import signal handlers when app is ready."""
        import leaves.signals
