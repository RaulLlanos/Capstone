from rest_framework import serializers
from .models import DireccionAsignada, Reagendamiento, HistorialAsignacion

class DireccionAsignadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionAsignada
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

class ReagendamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reagendamiento
        fields = "__all__"

class HistorialAsignacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialAsignacion
        fields = "__all__"

# Alias para compatibilidad
AsignacionSerializer = DireccionAsignadaSerializer
