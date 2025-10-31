# core/models.py
from django.db import models
from django.utils import timezone

# ==========================
# Mantiene tu modelo original
# ==========================
class Notificacion(models.Model):
    class Canal(models.TextChoices):
        NONE = "none", "Sin envío"
        EMAIL = "email", "Email"
        WEBHOOK = "webhook", "Webhook"
        SMS = "sms", "SMS"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    class Estado(models.TextChoices):
        PENDING = "pending", "Pendiente"
        QUEUED = "queued", "En cola"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falló"

    asignacion = models.ForeignKey(
        "asignaciones.DireccionAsignada",
        on_delete=models.CASCADE,
        related_name="notificaciones",
        null=True, blank=True,
    )
    canal = models.CharField(max_length=20, choices=Canal.choices, default=Canal.EMAIL)
    tipo = models.CharField(max_length=50, blank=True, default="")
    destino = models.CharField(max_length=255, blank=True, default="")
    asunto = models.CharField(max_length=255, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDING)
    provider = models.CharField(max_length=50, blank=True, default="")
    error = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notificaciones"
        ordering = ("-created_at",)
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"[{self.canal}/{self.status}] {self.tipo} → {self.destino or '(sin destino)'}"


# ==========================
# NUEVO: Configuración K/V
# ==========================
class Configuracion(models.Model):
    """
    K/V para parámetros globales.
    Ej: MIN_PASS_LENGTH=8
    """
    class Tipo(models.TextChoices):
        STR = "str", "Str"
        INT = "int", "Int"
        BOOL = "bool", "Bool"
        JSON = "json", "JSON"

    clave = models.CharField(max_length=64, unique=True)
    valor = models.TextField(blank=True, default="")
    tipo = models.CharField(max_length=16, choices=Tipo.choices, default=Tipo.STR)
    descripcion = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "configuracion"
        verbose_name = "Configuración"
        verbose_name_plural = "Configuración"

    def __str__(self):
        return f"{self.clave}={self.valor}"

    @classmethod
    def get_raw(cls, key: str, default=None):
        try:
            obj = cls.objects.get(clave__iexact=key)
            return obj.valor
        except Exception:
            return default

    @classmethod
    def get_int(cls, key: str, default: int = 0) -> int:
        v = cls.get_raw(key, None)
        try:
            return int(str(v).strip())
        except Exception:
            return default

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        v = cls.get_raw(key, None)
        s = str(v).strip().lower()
        if s in {"1", "true", "yes", "y", "on"}:
            return True
        if s in {"0", "false", "no", "n", "off"}:
            return False
        return default


# ==========================
# NUEVO: Logs del sistema
# ==========================
class LogSistema(models.Model):
    """
    Bitácora simple: (usuario, acción, fecha, detalle).
    """
    class Accion(models.TextChoices):
        CONFIG_CREATE = "CONFIG_CREATE", "Config: crear"
        CONFIG_UPDATE = "CONFIG_UPDATE", "Config: actualizar"
        CONFIG_DELETE = "CONFIG_DELETE", "Config: eliminar"

        USER_CREATE = "USER_CREATE", "Usuario: crear"
        USER_UPDATE = "USER_UPDATE", "Usuario: actualizar"
        USER_DEACTIVATE = "USER_DEACTIVATE", "Usuario: desactivar"
        USER_REACTIVATE = "USER_REACTIVATE", "Usuario: reactivar"
        USER_ROLE_UPDATE = "USER_ROLE_UPDATE", "Usuario: cambiar rol"
        USER_DELETE = "USER_DELETE", "Usuario: eliminar"

    usuario = models.ForeignKey(
        "usuarios.Usuario", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="logs"
    )
    accion = models.CharField(max_length=32, choices=Accion.choices)
    detalle = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "logs_sistema"
        ordering = ("-created_at", "-id")

    def __str__(self):
        who = getattr(self.usuario, "email", "system")
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.accion} by {who}"
