from rest_framework import serializers
from .models import Usuario, Tecnico, Visita, Reagendamiento, HistorialVisita, EvidenciaServicio

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = Usuario
        # Campos seguros (no exponemos is_superuser, password hash, etc.)
        fields = [
            'id', 'email', 'first_name', 'last_name', 'rut_usuario',
            'rol', 'is_active', 'is_staff', 'date_joined', 'password'
        ]
        read_only_fields = ['id', 'date_joined', 'is_staff']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        user.is_active = True
        user.save()
        return user

    def update(self, instance, validated_data):
        pwd = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance

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