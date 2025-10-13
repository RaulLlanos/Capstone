# core/models.py (solo el modelo Notificacion)
from django.db import models
from django.utils import timezone

class Notificacion(models.Model):
    class Canal(models.TextChoices):
        NONE = "none", "Sin envío"
        EMAIL = "email", "Email"
        WEBHOOK = "webhook", "Webhook"
        SMS = "sms", "SMS"

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
    destino = models.CharField(max_length=255, blank=True, default="")  # <— importante
    asunto = models.CharField(max_length=255, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)

    status = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDING)
    provider = models.CharField(max_length=50, blank=True, default="")  # <— importante
    error = models.TextField(blank=True, default="")                    # <— importante
    sent_at = models.DateTimeField(null=True, blank=True)               # <— importante

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notificaciones"  # <— coincide con tu error previo
        ordering = ("-created_at",)

    def __str__(self):
        return f"[{self.canal}/{self.status}] {self.tipo} → {self.destino or '(sin destino)'}"
