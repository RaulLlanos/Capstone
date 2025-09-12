from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Auditoria, AuditoriaServicio, AuditoriaCategoria, EvidenciaServicio
from asignaciones.models import HistorialAsignacion, EstadoAsignacion

class AuditoriaServicioInline(admin.TabularInline):
    model = AuditoriaServicio
    extra = 0

class EvidenciaServicioInline(admin.TabularInline):
    model = EvidenciaServicio
    extra = 0
    autocomplete_fields = ("asignacion", "usuario")

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "asignacion", "direccion_cliente", "marca", "tecnologia", "estado_cliente", "created_at")
    list_filter  = ("marca", "tecnologia", "estado_cliente", "created_at")
    search_fields = ("direccion_cliente", "rut_cliente", "id_vivienda")
    autocomplete_fields = ("asignacion",)

    fieldsets = (
        (_("Dirección"), {"fields": ("asignacion",)}),
        (_("Snapshot (se completa automáticamente)"), {
            "fields": ("marca", "tecnologia", "rut_cliente", "id_vivienda", "direccion_cliente"),
            "description": "Se llena desde la Dirección seleccionada al guardar; no es necesario editarlo."
        }),
        (_("Estado del cliente"), {"fields": ("estado_cliente", "ont_modem_ok")}),
        (_("Bloques (JSON)"), {"fields": ("bloque_agendamiento", "bloque_llegada", "bloque_proceso", "bloque_config", "bloque_cierre", "percepcion")}),
        (_("Problema"), {"fields": ("descripcion_problema",)}),
        (_("Meta"), {"fields": ("created_at",)}),
    )
    readonly_fields = ("marca", "tecnologia", "rut_cliente", "id_vivienda", "direccion_cliente", "created_at")
    inlines = [AuditoriaServicioInline, EvidenciaServicioInline]

    def save_model(self, request, obj, form, change):
        # Snapshot: si los fields están vacíos, cópialos de la dirección
        asign = obj.asignacion
        if asign:
            if not obj.marca:             obj.marca = asign.marca
            if not obj.tecnologia:        obj.tecnologia = asign.tecnologia
            if not obj.rut_cliente:       obj.rut_cliente = asign.rut_cliente
            if not obj.id_vivienda:       obj.id_vivienda = asign.id_vivienda
            if not obj.direccion_cliente: obj.direccion_cliente = asign.direccion

        super().save_model(request, obj, form, change)

        # Marca la dirección como VISITADA y deja historial
        asign.estado = EstadoAsignacion.VISITADA
        asign.save(update_fields=["estado", "updated_at"])
        HistorialAsignacion.objects.create(
            asignacion=asign,
            accion=HistorialAsignacion.Accion.AUDITORIA_CREADA,
            detalles=f"Auditoría {obj.id} creada desde admin.",
            usuario=getattr(request, "user", None),
        )

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
    list_display = ("id", "auditoria", "asignacion", "tipo", "usuario", "created_at")
    list_filter  = ("tipo", "created_at")
    search_fields = ("asignacion__direccion", "auditoria__id", "usuario__email")
    autocomplete_fields = ("auditoria", "asignacion", "usuario")
