from django.contrib import admin
from .models import Auditoria, AuditoriaServicio, AuditoriaCategoria, EvidenciaServicio

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "asignacion", "direccion_cliente", "marca", "tecnologia", "estado_cliente", "created_at")
    list_filter  = ("marca", "tecnologia", "estado_cliente", "created_at")
    search_fields = ("direccion_cliente", "rut_cliente", "id_vivienda")

@admin.register(AuditoriaServicio)
class AuditoriaServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "auditoria", "servicio")
    list_filter  = ("servicio",)
    search_fields = ("auditoria__id",)

@admin.register(AuditoriaCategoria)
class AuditoriaCategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "auditoria_servicio", "categoria", "extra")
    search_fields = ("categoria", "extra")

@admin.register(EvidenciaServicio)
class EvidenciaServicioAdmin(admin.ModelAdmin):
    list_display = ("id", "auditoria", "asignacion", "tipo", "archivo", "usuario", "created_at")
    list_filter  = ("tipo", "created_at")
    search_fields = ("asignacion__direccion", "auditoria__id", "usuario__email")
    autocomplete_fields = ("auditoria", "asignacion", "usuario")
