# core/admin.py
from django.contrib import admin
from .models import Notificacion

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "tipo", "canal", "destino", "status", "provider", "created_at", "sent_at",
    )
    list_filter = ("status", "canal", "created_at")
    search_fields = ("destino", "tipo", "provider", "error")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "sent_at", "error")
