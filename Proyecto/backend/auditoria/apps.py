# auditoria/apps.py
from django.apps import AppConfig

class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'

    def ready(self):
        # Evita romper el arranque si signals tiene errores mientras desarrollas
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
