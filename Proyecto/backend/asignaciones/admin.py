from django.contrib import admin

from .models import DireccionAsignada

# Register your models here.

@admin.register(DireccionAsignada)
class DireccionAsignadaAdmin(admin.ModelAdmin):
    list_display = ('id','direccion','marca','tecnologia','encuesta','asignado_a','estado','created_at')
    list_filter = ('marca','tecnologia','encuesta','estado','created_at')
    search_fields = ('direccion','rut_cliente','id_vivienda','id_qualtrics')
