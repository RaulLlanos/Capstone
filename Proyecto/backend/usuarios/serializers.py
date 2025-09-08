# usuarios/serializers.py
from rest_framework import serializers
from .models import Usuario, Tecnico, Visita, Reagendamiento, HistorialVisita, EvidenciaServicio


class UsuarioSerializer(serializers.ModelSerializer):
    # Permite setear password en create/update (write_only)
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = Usuario
        # Campos expuestos (seguros): NO exponemos hash ni is_superuser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'rut_usuario',
            'rol', 'is_active', 'is_staff', 'date_joined', 'password'
        ]
        read_only_fields = ['id', 'date_joined', 'is_staff']  # is_staff lo maneja solo admin

    def create(self, validated_data):
        """
        Crear usuario:
        - Hashea password si viene.
        - Activa el usuario por defecto.
        Nota: el control de "quién puede crear" lo hace la ViewSet (permisos).
        """
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        user.is_active = True
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Actualizar usuario:
        - Si NO es admin/auditor, no dejamos que cambien campos sensibles:
            rol / is_staff / is_superuser
        - Hasheamos password si llega.
        """
        request = self.context.get('request')
        is_admin_or_auditor = bool(request and getattr(request.user, 'rol', None) in ('admin', 'auditor'))

        # Blindar campos sensibles si el que actualiza no es admin/auditor
        if not is_admin_or_auditor:
            for sensitive in ('rol', 'is_staff', 'is_superuser'):
                validated_data.pop(sensitive, None)

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
