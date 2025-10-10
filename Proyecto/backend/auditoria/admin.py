# auditoria/admin.py
from django.contrib import admin
from .models import AuditoriaVisita


# --- Filtros por campos de la asignación relacionada ---
class MarcaListFilter(admin.SimpleListFilter):
    title = "marca"
    parameter_name = "marca"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        valores = (
            qs.values_list("asignacion__marca", flat=True)
              .distinct()
              .order_by("asignacion__marca")
        )
        return [(v, v) for v in valores if v]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(asignacion__marca=self.value())
        return queryset


class TecnologiaListFilter(admin.SimpleListFilter):
    title = "tecnología"
    parameter_name = "tecnologia"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        valores = (
            qs.values_list("asignacion__tecnologia", flat=True)
              .distinct()
              .order_by("asignacion__tecnologia")
        )
        return [(v, v) for v in valores if v]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(asignacion__tecnologia=self.value())
        return queryset


@admin.register(AuditoriaVisita)
class AuditoriaVisitaAdmin(admin.ModelAdmin):
    list_display = ("id", "asignacion", "estado_cliente", "marca", "tecnologia", "created_at")

    search_fields = (
        "asignacion__direccion",
        "asignacion__rut_cliente",
        "asignacion__comuna",
    )

    list_filter = ("estado_cliente", MarcaListFilter, TecnologiaListFilter, "created_at")
    autocomplete_fields = ("asignacion",)

    @admin.display(ordering="asignacion__marca", description="Marca")
    def marca(self, obj):
        return getattr(obj.asignacion, "marca", None)

    @admin.display(ordering="asignacion__tecnologia", description="Tecnología")
    def tecnologia(self, obj):
        return getattr(obj.asignacion, "tecnologia", None)
