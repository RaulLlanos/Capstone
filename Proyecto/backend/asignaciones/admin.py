from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import (
    DireccionAsignada, Reagendamiento, HistorialAsignacion,
    EstadoAsignacion, BloqueHorario
)
from .comunas import zona_para_comuna, COMUNAS_SANTIAGO
from usuarios.models import Usuario

class DireccionAsignadaAdminForm(forms.ModelForm):
    comuna = forms.ChoiceField(choices=[(c, c) for c in COMUNAS_SANTIAGO])

    class Meta:
        model = DireccionAsignada
        fields = "__all__"

@admin.register(DireccionAsignada)
class DireccionAsignadaAdmin(admin.ModelAdmin):
    form = DireccionAsignadaAdminForm

    list_display = (
        "id", "fecha", "direccion", "comuna", "zona",
        "marca", "tecnologia", "encuesta",
        "asignado_a", "estado", "reagendado_fecha", "reagendado_bloque",
        "created_at",
    )
    list_filter = ("marca", "tecnologia", "encuesta", "estado", "zona", "comuna", "created_at")
    search_fields = ("direccion", "comuna", "rut_cliente", "id_vivienda", "id_qualtrics")
    autocomplete_fields = ("asignado_a",)
    ordering = ("-created_at",)

    fieldsets = (
        ("Información del cliente", {
            "fields": ("fecha", "direccion", "comuna", "zona", "marca", "tecnologia", "rut_cliente", "id_vivienda")
        }),
        ("Encuesta / trazabilidad", {
            "fields": ("encuesta", "id_qualtrics")
        }),
        ("Asignación", {
            "fields": ("asignado_a", "estado")
        }),
        ("Reagendamiento (si aplica)", {
            "fields": ("reagendado_fecha", "reagendado_bloque"),
            "description": "Estos campos solo se usan cuando el cliente reagenda."
        }),
        ("Metadatos", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at", "zona")

    # NUEVO: si el usuario no es administrador, no puede editar asignado_a/estado en admin
    def get_readonly_fields(self, request, obj=None):
        ro = list(self.readonly_fields)
        if getattr(request.user, "rol", None) != "administrador":
            ro += ["asignado_a", "estado"]
        return ro

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "asignado_a":
            kwargs["queryset"] = Usuario.objects.filter(rol="tecnico").order_by("first_name", "last_name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Fecha futura
        if obj.fecha and obj.fecha < timezone.localdate():
            raise ValidationError({"fecha": "La fecha no puede ser en el pasado."})

        # Calcular zona por comuna
        if obj.comuna:
            try:
                obj.zona = zona_para_comuna(obj.comuna)
            except Exception:
                raise ValidationError({"comuna": "Comuna no válida para Santiago."})

        creating = obj.pk is None

        super().save_model(request, obj, form, change)

        if creating:
            HistorialAsignacion.objects.create(
                asignacion=obj,
                accion=HistorialAsignacion.Accion.CREADA,
                detalles="Creada desde admin.",
                usuario=getattr(request, "user", None),
            )
        elif "asignado_a" in (form.changed_data or []):
            if obj.asignado_a_id:
                HistorialAsignacion.objects.create(
                    asignacion=obj,
                    accion=HistorialAsignacion.Accion.ASIGNADA_TECNICO,
                    detalles=f"Asignada a {obj.asignado_a.email}",
                    usuario=getattr(request, "user", None),
                )
            else:
                HistorialAsignacion.objects.create(
                    asignacion=obj,
                    accion=HistorialAsignacion.Accion.DESASIGNADA,
                    detalles="Desasignada desde admin.",
                    usuario=getattr(request, "user", None),
                )

@admin.register(Reagendamiento)
class ReagendamientoAdmin(admin.ModelAdmin):
    list_display = ("id", "asignacion", "fecha_anterior", "bloque_anterior", "fecha_nueva", "bloque_nuevo", "usuario", "created_at")
    list_filter  = ("bloque_nuevo", "created_at")
    search_fields = ("asignacion__direccion", "usuario__email")
    autocomplete_fields = ("asignacion", "usuario")

    fieldsets = (
        ("Dirección", {"fields": ("asignacion",)}),
        ("Reagendamiento", {"fields": ("fecha_anterior", "bloque_anterior", "fecha_nueva", "bloque_nuevo", "motivo")}),
        ("Meta", {"fields": ("usuario", "created_at")}),
    )
    readonly_fields = ("created_at",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "usuario":
            kwargs["queryset"] = Usuario.objects.filter(rol="tecnico").order_by("first_name", "last_name")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.fecha_nueva and obj.fecha_nueva < timezone.localdate():
            raise ValidationError({"fecha_nueva": "La fecha no puede ser en el pasado."})

        if obj.asignacion and (not obj.fecha_anterior or not obj.bloque_anterior):
            obj.fecha_anterior  = obj.fecha_anterior  or (obj.asignacion.reagendado_fecha or obj.asignacion.fecha)
            obj.bloque_anterior = obj.bloque_anterior or obj.asignacion.reagendado_bloque

        if not obj.usuario_id:
            obj.usuario = request.user if getattr(request.user, "rol", None) == "tecnico" else obj.usuario

        super().save_model(request, obj, form, change)

        asignacion = obj.asignacion
        asignacion.reagendado_fecha  = obj.fecha_nueva
        asignacion.reagendado_bloque = obj.bloque_nuevo
        asignacion.estado = EstadoAsignacion.REAGENDADA
        asignacion.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado", "updated_at"])

        HistorialAsignacion.objects.create(
            asignacion=asignacion,
            accion=HistorialAsignacion.Accion.REAGENDADA,
            detalles=f"Reagendada a {obj.fecha_nueva} {obj.bloque_nuevo}. Motivo: {obj.motivo}",
            usuario=getattr(request, "user", None),
        )

@admin.register(HistorialAsignacion)
class HistorialAsignacionAdmin(admin.ModelAdmin):
    list_display = ("id", "asignacion", "accion", "detalles", "usuario", "created_at")
    list_filter  = ("accion", "created_at")
    search_fields = ("detalles", "asignacion__direccion", "usuario__email")
    readonly_fields = ("asignacion", "accion", "detalles", "usuario", "created_at")

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
