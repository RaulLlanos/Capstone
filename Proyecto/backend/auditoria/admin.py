from django.contrib import admin

from .models import AuditoriaInstalacion

# Register your models here.

@admin.register(AuditoriaInstalacion)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ['id', 'direccion_cliente', 'marca', 'tecnologia', 'estado_cliente', 'fecha_auditoria']
    list_filter = ['marca', 'tecnologia', 'estado_cliente', 'fecha_auditoria']
    search_fields = ['direccion_cliente', 'rut_cliente', 'nombre_auditor']
    