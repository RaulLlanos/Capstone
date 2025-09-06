from django.contrib import admin
from .models import AuditoriaVisita, Issue

@admin.register(AuditoriaVisita)
class AuditoriaVisitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'direccion_cliente', 'marca', 'tecnologia', 'estado_cliente', 'created_at')
    list_filter = ('marca', 'tecnologia', 'estado_cliente', 'created_at')
    search_fields = ('direccion_cliente', 'rut_cliente', 'id_vivienda', 'nombre_auditor')

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'auditoria', 'servicio', 'detalle')
    search_fields = ('servicio', 'detalle')
