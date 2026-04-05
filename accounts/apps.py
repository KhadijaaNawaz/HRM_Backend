from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'
    verbose_name = 'Accounts'

    def ready(self):
        """Import signals when app is ready."""
        import accounts.signals
