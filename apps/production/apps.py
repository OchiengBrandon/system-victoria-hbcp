from django.apps import AppConfig


class ProductionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.production'

    def ready(self):
        # Import the signals module to ensure signals are connected
        import apps.production.signals  # Ensure this line is included