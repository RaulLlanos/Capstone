from rest_framework import serializers
from .models import DireccionAsignada

class DireccionAsignadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionAsignada
        fields = '__all__'
        read_only_fields = (
            'created_at', 'updated_at', 'estado',
            'reagendado_fecha', 'reagendado_bloque',  # ← solo vía /reagendar
            'asignado_a',                              # ← el técnico se asigna con /asignarme
        )
