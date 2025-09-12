from django.contrib import admin
from .models import DireccionAsignada, Reagendamiento, HistorialAsignacion

@admin.register(DireccionAsignada)
class DireccionAsignadaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "fecha", "direccion", "comuna", "zona",
        "marca", "tecnologia", "encuesta",
        "asignado_a", "estado", "reagendado_fecha", "reagendado_bloque",
        "created_at",
    )
    list_filter = ("marca", "tecnologia", "encuesta", "estado", "zona", "comuna", "created_at")
    search_fields = ("direccion", "comuna", "rut_cliente", "id_vivienda", "id_qualtrics")
    autocomplete_fields = ("asignado_a",)

@admin.register(Reagendamiento)
class ReagendamientoAdmin(admin.ModelAdmin):
    list_display = ("id", "asignacion", "fecha_anterior", "bloque_anterior", "fecha_nueva", "bloque_nuevo", "usuario", "created_at")
    list_filter  = ("bloque_nuevo", "created_at")
    search_fields = ("asignacion__direccion", "usuario__email")

@admin.register(HistorialAsignacion)
class HistorialAsignacionAdmin(admin.ModelAdmin):
    list_display = ("id", "asignacion", "accion", "detalles", "usuario", "created_at")
    list_filter  = ("accion", "created_at")
    search_fields = ("detalles", "asignacion__direccion", "usuario__email")
