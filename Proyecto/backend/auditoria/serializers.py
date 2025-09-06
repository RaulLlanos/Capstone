# auditoria/serializers.py
from rest_framework import serializers
from .models import AuditoriaVisita, Issue

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'


class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    issues = IssueSerializer(many=True, required=False)

    class Meta:
        model = AuditoriaVisita
        fields = '__all__'
        # Los campos snapshot vienen desde la asignación (no los envía el cliente)
        read_only_fields = (
            'created_at',
            'marca', 'tecnologia',
            'rut_cliente', 'id_vivienda', 'direccion_cliente',
        )

    # --- helpers internos ---
    def _validate_image(self, fileobj, field_name):
        """Valida tipo/size de una imagen si viene en la request."""
        if not fileobj:
            return
        content_type = getattr(fileobj, 'content_type', '') or ''
        if not content_type.startswith('image/'):
            raise serializers.ValidationError({field_name: 'Solo imágenes.'})
        size = getattr(fileobj, 'size', 0) or 0
        if size > 10 * 1024 * 1024:  # 10 MB
            raise serializers.ValidationError({field_name: 'Máximo 10MB por imagen.'})

    def validate(self, attrs):
        """
        Chequeos:
        - Permiso: técnico solo puede crear auditoría sobre su propia asignación.
        - (Opcional) Validación de imágenes si vienen en este mismo POST.
        """
        request = self.context.get('request')
        asignacion = attrs.get('asignacion')

        if request and getattr(request.user, 'rol', None) == 'tecnico':
            if asignacion and asignacion.asignado_a_id != request.user.id:
                raise serializers.ValidationError('No autorizado para esta asignación.')

        # Si el cliente decide crear auditoría **con** fotos en el mismo POST (multipart),
        # validamos aquí. (Si suben fotos por /upload_fotos/, esto no corre y deberás validar en la vista.)
        if request and hasattr(request, 'FILES'):
            self._validate_image(request.FILES.get('foto_1'), 'foto_1')
            self._validate_image(request.FILES.get('foto_2'), 'foto_2')
            self._validate_image(request.FILES.get('foto_3'), 'foto_3')

        # Alternativa cuando DRF pasa archivos en initial_data (según parseador)
        f1 = self.initial_data.get('foto_1') if hasattr(self, 'initial_data') else None
        f2 = self.initial_data.get('foto_2') if hasattr(self, 'initial_data') else None
        f3 = self.initial_data.get('foto_3') if hasattr(self, 'initial_data') else None
        for f, name in ((f1, 'foto_1'), (f2, 'foto_2'), (f3, 'foto_3')):
            # Algunos parsers dejan strings vacíos cuando no hay archivo; ignóralos.
            if hasattr(f, 'content_type'):
                self._validate_image(f, name)

        return attrs

    def create(self, validated_data):
        issues_data = validated_data.pop('issues', [])
        asignacion = validated_data['asignacion']

        # Construimos la auditoría inyectando el snapshot desde la asignación
        auditoria = AuditoriaVisita.objects.create(
            asignacion=asignacion,
            nombre_auditor=validated_data.get('nombre_auditor', ''),
            estado_cliente=validated_data.get('estado_cliente', ''),

            # SNAPSHOT desde la asignación:
            marca=asignacion.marca,
            tecnologia=asignacion.tecnologia,
            rut_cliente=asignacion.rut_cliente,
            id_vivienda=asignacion.id_vivienda,
            direccion_cliente=asignacion.direccion,
        )

        # Issues anidados (opcionales)
        for it in issues_data:
            Issue.objects.create(auditoria=auditoria, **it)

        return auditoria
