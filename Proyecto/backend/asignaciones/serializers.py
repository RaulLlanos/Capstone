from django.utils import timezone
from rest_framework import serializers
from .models import DireccionAsignada
from .comunas import zona_para_comuna, COMUNAS_SANTIAGO

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
    comuna = serializers.ChoiceField(choices=COMUNAS_SANTIAGO, required=True)

    class Meta:
        model = DireccionAsignada
        fields = "__all__"
        read_only_fields = (
            "created_at", "updated_at", "estado",
            "reagendado_fecha", "reagendado_bloque",
            "asignado_a",          # el técnico se asigna vía acciones
            "zona",                # calculada automáticamente
        )

    def validate(self, attrs):
        # Fecha no puede ser en el pasado
        fecha = attrs.get("fecha")
        if fecha and fecha < timezone.localdate():
            raise serializers.ValidationError({"fecha": "La fecha no puede ser en el pasado."})

        # Comuna obligatoria en creación
        comuna = attrs.get("comuna")
        if self.instance is None and not comuna:
            raise serializers.ValidationError({"comuna": "Debe indicar la comuna."})

        # Calcular zona por comuna (en create o en update cuando cambia)
        comuna_eff = comuna if comuna is not None else getattr(self.instance, "comuna", None)
        if comuna_eff:
            try:
                attrs["zona"] = zona_para_comuna(comuna_eff)
            except ValueError:
                raise serializers.ValidationError({"comuna": "Comuna no válida para Santiago."})

        return attrs
