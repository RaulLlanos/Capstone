from rest_framework import serializers
from .models import Usuario, Tecnico, Visita, Reagendamiento, HistorialVisita, EvidenciaServicio

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class TecnicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tecnico
        fields = '__all__'

class VisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visita
        fields = '__all__'

class ReagendamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reagendamiento
        fields = '__all__'

class HistorialVisitaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialVisita
        fields = '__all__'

class EvidenciaServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaServicio
        fields = '__all__'