# asignaciones/admin.py
from django.contrib import admin
from django.db import transaction

from .models import DireccionAsignada, HistorialAsignacion
from usuarios.models import Usuario


@admin.register(DireccionAsignada)
class DireccionAsignadaAdmin(admin.ModelAdmin):
    """
    Panel /admin para DireccionAsignada.

    - Filtros y búsqueda útiles
    - Acción masiva: desasignar (traza DESASIGNADA)
    - En /admin/ sólo los 'administrador' (o superuser) editan.
      Técnicos siguen operando por API (no cambia nada del front).
    """
    list_display = (
        "id",
        "fecha",
        "estado",
        "bloque_label",
        "direccion",
        "comuna",
        "zona",
        "marca",
        "tecnologia",
        "asignado_a",
        "created_at",
    )
    list_filter = (
        "estado",
        "marca",
        "tecnologia",
        "comuna",
        "zona",
        ("fecha", admin.DateFieldListFilter),
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "direccion",
        "comuna",
        "rut_cliente",
        "id_vivienda",
        "id_qualtrics",
        "encuesta",
    )
    readonly_fields = ("created_at", "updated_at")

    actions = ["accion_desasignar"]

    # ---------- helpers de UI ----------
    def bloque_label(self, obj):
        b = (obj.reagendado_bloque or "").strip()
        if b == "10-13":
            return "10:00–13:00"
        if b == "14-18":
            return "14:00–18:00"
        return "-"
    bloque_label.short_description = "Bloque"

    # ---------- permisos de edición SÓLO para /admin ----------
    def get_readonly_fields(self, request, obj=None):
        """
        Admin UI solamente:
        - 'administrador' o superuser pueden editar.
        - El resto (p.ej. técnico) ve readonly en /admin/.
        (La API NO se toca: técnico mantiene sus POST/acciones).
        """
        user = getattr(request, "user", None)
        es_admin = bool(user and getattr(user, "rol", None) == "administrador")
        es_super = bool(user and getattr(user, "is_superuser", False))
        if es_admin or es_super:
            return self.readonly_fields

        # todo lo demás es readonly en /admin/
        campos = [f.name for f in DireccionAsignada._meta.fields]
        return tuple(set(campos) | set(self.readonly_fields))

    # ---------- acciones masivas ----------
    @admin.action(description="Desasignar visitas seleccionadas (volver a PENDIENTE)")
    def accion_desasignar(self, request, queryset):
        """
        Quita el técnico y vuelve la visita a PENDIENTE.
        Deja trazabilidad en HistorialAsignacion con accion=DESASIGNADA.
        """
        count = 0
        with transaction.atomic():
            for obj in queryset.select_related("asignado_a"):
                prev_tec = obj.asignado_a
                obj.asignado_a = None
                obj.estado = "PENDIENTE"
                obj.save(update_fields=["asignado_a", "estado", "updated_at"])

                HistorialAsignacion.objects.create(
                    asignacion=obj,
                    accion=HistorialAsignacion.Accion.DESASIGNADA,  # ← ya existe
                    detalles=(
                        f"Desasignada por admin desde el sitio de administración. "
                        f"{'Antes: ' + prev_tec.email if prev_tec else 'Sin técnico previo'}."
                    ),
                    usuario=request.user,
                )
                count += 1

        self.message_user(request, f"{count} visitas desasignadas correctamente.")

    # ordenar por defecto
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("fecha", "id")


@admin.register(HistorialAsignacion)
class HistorialAsignacionAdmin(admin.ModelAdmin):
    """
    Panel /admin para HistorialAsignacion.
    Muestra todo el log, incluyendo DESASIGNADA y EDITADA.
    """
    list_display = (
        "id",
        "asignacion_id",
        "accion",
        "detalles",
        "usuario",
        "created_at",
    )
    list_filter = (
        "accion",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = (
        "detalles",
        "asignacion__direccion",
        "asignacion__comuna",
        "usuario__email",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at", "-id")
