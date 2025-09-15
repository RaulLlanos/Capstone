from rest_framework import serializers
from .models import AuditoriaVisita, Issue


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = "__all__"


class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    """
    - Crea auditoría sobre una DireccionAsignada.
    - Inyecta snapshot (marca/tecnología/rut/id_vivienda/dirección) desde la asignación.
    - Permite issues anidados opcionales.
    - Valida fotos opcionalmente (si vienen en el mismo POST).
    """
    issues = IssueSerializer(many=True, required=False)

    class Meta:
        model = AuditoriaVisita
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "marca", "tecnologia",
            "rut_cliente", "id_vivienda", "direccion_cliente",
        )

    # --- helpers de validación de imagen ---
    def _validate_image(self, fileobj, field_name):
        if not fileobj:
            return
        content_type = getattr(fileobj, "content_type", "") or ""
        if not content_type.startswith("image/"):
            raise serializers.ValidationError({field_name: "Solo imágenes."})
        size = getattr(fileobj, "size", 0) or 0
        if size > 10 * 1024 * 1024:  # 10 MB
            raise serializers.ValidationError({field_name: "Máximo 10MB por imagen."})

    def validate(self, attrs):
        """
        Chequeos:
        - Si es técnico, solo puede crear sobre su propia asignación.
        - Valida fotos si vienen en este mismo POST.
        """
        request = self.context.get("request")
        asignacion = attrs.get("asignacion")

        if request and getattr(request.user, "rol", None) == "tecnico":
            if asignacion and asignacion.asignado_a_id != request.user.id:
                raise serializers.ValidationError("No autorizado para esta asignación.")

        # Validación de imágenes (multipart)
        if request and hasattr(request, "FILES"):
            self._validate_image(request.FILES.get("foto_1"), "foto_1")
            self._validate_image(request.FILES.get("foto_2"), "foto_2")
            self._validate_image(request.FILES.get("foto_3"), "foto_3")

        # Algunos parsers dejan archivos en initial_data
        if hasattr(self, "initial_data"):
            for fname in ("foto_1", "foto_2", "foto_3"):
                f = self.initial_data.get(fname)
                if hasattr(f, "content_type"):
                    self._validate_image(f, fname)

        return attrs

    def create(self, validated_data):
        issues_data = validated_data.pop("issues", [])
        asignacion = validated_data["asignacion"]

        # Construye auditoría con snapshot desde la asignación
        auditoria = AuditoriaVisita.objects.create(
            asignacion=asignacion,
            nombre_auditor=validated_data.get("nombre_auditor", ""),
            estado_cliente=validated_data.get("estado_cliente", ""),
            marca=asignacion.marca,
            tecnologia=asignacion.tecnologia,
            rut_cliente=asignacion.rut_cliente,
            id_vivienda=asignacion.id_vivienda,
            direccion_cliente=asignacion.direccion,
            # Si el request venía multipart con fotos, DRF setea estos campos solo si están en validated_data;
            # para soportar eso vía serializer, podrías añadirlos a validated_data si te interesa.
            foto_1=validated_data.get("foto_1"),
            foto_2=validated_data.get("foto_2"),
            foto_3=validated_data.get("foto_3"),
        )

        # Crea issues anidados
        for it in issues_data:
            Issue.objects.create(auditoria=auditoria, **it)

        return auditoria
