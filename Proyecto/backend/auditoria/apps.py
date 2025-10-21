from django.apps import AppConfig

class AuditoriaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditoria"

    def ready(self):
        # Registra señales
        from . import signals  # noqa
