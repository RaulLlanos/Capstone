# asignaciones/serializers.py
from rest_framework import serializers
from .models import DireccionAsignada

class DireccionAsignadaListaSerializer(serializers.ModelSerializer):
    tecnico = serializers.SerializerMethodField()

    class Meta:
        model = DireccionAsignada
        fields = [
            "id", "fecha", "tecnologia", "marca",
            "direccion", "comuna", "zona",
            "rut_cliente", "id_vivienda",
            "estado", "asignado_a", "tecnico",
        ]

    def get_tecnico(self, obj):
        u = obj.asignado_a
        if not u:
            return None
        return {
            "id": u.id,
            "nombre": f"{u.first_name} {u.last_name}".strip(),
            "email": u.email,
        }

class DireccionAsignadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionAsignada
        fields = "__all__"
        read_only_fields = (
            "created_at", "updated_at", "estado",
            "reagendado_fecha", "reagendado_bloque",  # ← solo vía /reagendar o /estado_cliente
            "asignado_a",                              # ← el técnico se asigna con /asignarme
        )
