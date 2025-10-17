# core/admin.py
from django.contrib import admin
from core.models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tipo",
        "canal",
        "destino",
        "provider",
        "status",
        "asignacion_id",
        "created_at",
        "sent_at",
    )
    list_filter = ("canal", "status", "provider", "created_at")
    search_fields = ("destino", "tipo", "asunto", "payload")
    readonly_fields = ("created_at", "updated_at", "sent_at", "error")
