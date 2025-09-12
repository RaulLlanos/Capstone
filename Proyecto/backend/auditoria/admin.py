from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# Modelos actuales del app auditoria
from .models import AuditoriaVisita, Issue

# Importes opcionales desde asignaciones (si existen en tu código)
# Evitamos romper el import si todavía no tienes esos modelos.
try:
    from asignaciones.models import DireccionAsignada, HistorialAsignacion, EstadoAsignacion
except Exception:  # ImportError o AttributeError
    DireccionAsignada = None
    HistorialAsignacion = None
    EstadoAsignacion = None


class IssueInline(admin.TabularInline):
    model = Issue
    extra = 0


@admin.register(AuditoriaVisita)
class AuditoriaVisitaAdmin(admin.ModelAdmin):
    """
    Admin para AuditoriaVisita (antes "Auditoria").
    - Muestra snapshot (marca/tecnología/rut/id_vivienda/dirección)
    - Llenado automático del snapshot desde la asignación al guardar
    - Marca la DireccionAsignada como VISITADA y deja historial (si el modelo existe)
    """
    list_display = (
        "id",
        "asignacion",
        "direccion_cliente",
        "marca",
        "tecnologia",
        "estado_cliente",
        "created_at",
    )
    list_filter = ("marca", "tecnologia", "estado_cliente", "created_at")
    search_fields = ("direccion_cliente", "rut_cliente", "id_vivienda", "nombre_auditor")
    autocomplete_fields = ("asignacion",)
    inlines = [IssueInline]

    fieldsets = (
        (_("Dirección / Asignación"), {"fields": ("asignacion", "nombre_auditor", "estado_cliente")}),
        (_("Snapshot (se completa automáticamente)"), {
            "fields": ("marca", "tecnologia", "rut_cliente", "id_vivienda", "direccion_cliente"),
            "description": _("Se llena desde la Dirección seleccionada al guardar; no es necesario editarlo.")
        }),
        (_("Evidencias (opcionales)"), {"fields": ("foto_1", "foto_2", "foto_3")}),
        (_("Meta"), {"fields": ("created_at",)}),
    )
    readonly_fields = ("marca", "tecnologia", "rut_cliente", "id_vivienda", "direccion_cliente", "created_at")

    def save_model(self, request, obj, form, change):
        """
        - Completa snapshot desde la asignación (si faltan valores)
        - Marca la asignación como VISITADA
        - Crea un HistorialAsignacion si el modelo está disponible
        """
        asign = obj.asignacion
        if asign:
            # Snapshot si faltan
            if not obj.marca:
                obj.marca = getattr(asign, "marca", "") or ""
            if not obj.tecnologia:
                obj.tecnologia = getattr(asign, "tecnologia", "") or ""
            if not obj.rut_cliente:
                obj.rut_cliente = getattr(asign, "rut_cliente", "") or ""
            if not obj.id_vivienda:
                obj.id_vivienda = getattr(asign, "id_vivienda", "") or ""
            if not obj.direccion_cliente:
                obj.direccion_cliente = getattr(asign, "direccion", "") or ""

        super().save_model(request, obj, form, change)

        # Marca VISITADA + historial (si esos modelos existen en tu código)
        try:
            if asign and EstadoAsignacion and HistorialAsignacion:
                if getattr(asign, "estado", None) != getattr(EstadoAsignacion, "VISITADA", "VISITADA"):
                    asign.estado = getattr(EstadoAsignacion, "VISITADA", "VISITADA")
                    asign.save(update_fields=["estado", "updated_at"])

                # Esquema de acciones común: AUDITORIA_CREADA. Si no existe, cae a 'auditoria_creada'.
                accion_val = getattr(getattr(HistorialAsignacion, "Accion", None), "AUDITORIA_CREADA", "auditoria_creada")
                HistorialAsignacion.objects.create(
                    asignacion=asign,
                    accion=accion_val,
                    detalles=f"Auditoría #{obj.id} creada desde admin.",
                    usuario=getattr(request, "user", None),
                )
        except Exception:
            # No interrumpir el guardado del admin si el historial no existe o cambia
            pass


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("id", "auditoria", "servicio", "detalle")
    list_filter = ("servicio",)
    search_fields = ("auditoria__id", "servicio", "detalle")
