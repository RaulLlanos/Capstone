# core/admin.py
from django.contrib import admin
from core.models import Notificacion, Configuracion, LogSistema


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


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ("clave", "valor", "tipo", "updated_at", "created_at")
    search_fields = ("clave", "valor", "descripcion")
    list_filter = ("tipo",)
    ordering = ("clave",)


@admin.register(LogSistema)
class LogSistemaAdmin(admin.ModelAdmin):
    list_display = ("id", "accion", "usuario", "created_at", "detalle")
    search_fields = ("detalle", "usuario__email", "accion")
    list_filter = ("accion", ("created_at", admin.DateFieldListFilter))
    ordering = ("-created_at", "-id")
