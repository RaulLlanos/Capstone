from datetime import date
from django.utils import timezone
from rest_framework import serializers

from .models import DireccionAsignada, HistorialAsignacion
from usuarios.models import Usuario


class DireccionAsignadaSerializer(serializers.ModelSerializer):
    """Serializer principal de la visita/asignación."""
    class Meta:
        model = DireccionAsignada
        fields = [
            "id", "fecha", "tecnologia", "marca",
            "rut_cliente", "id_vivienda", "direccion", "comuna",
            "zona", "encuesta", "id_qualtrics",
            "estado",
            "reagendado_fecha", "reagendado_bloque",
            "created_at", "updated_at",
            "asignado_a",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_fecha(self, value):
        # Permitir null (pendiente sin fecha), pero si viene, no puede ser pasada
        if value and value < timezone.localdate():
            raise serializers.ValidationError("La fecha no puede ser pasada.")
        return value

    def validate(self, attrs):
        # Normalizaciones simples
        z = attrs.get("zona")
        if z:
            attrs["zona"] = z.upper()
        m = attrs.get("marca")
        if m:
            attrs["marca"] = m.upper()
        t = attrs.get("tecnologia")
        if t:
            attrs["tecnologia"] = t.upper()
        e = attrs.get("encuesta")
        if e:
            attrs["encuesta"] = e.lower()
        return attrs


class HistorialAsignacionSerializer(serializers.ModelSerializer):
    usuario_email = serializers.SerializerMethodField()
    asignacion_info = serializers.SerializerMethodField()

    # Campos “derivados” desde la asignación para filtros/reportes
    marca = serializers.CharField(source="asignacion.marca", read_only=True)
    tecnologia = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    direccion = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    fecha = serializers.DateField(source="asignacion.fecha", read_only=True)
    bloque = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)

    class Meta:
        model = HistorialAsignacion
        fields = [
            "id", "accion", "detalles", "created_at",
            "usuario_id", "usuario_email",
            "asignacion_id", "asignacion_info",
            # derivados
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque",
        ]

    def get_usuario_email(self, obj):
        return getattr(obj.usuario, "email", None)

    def get_asignacion_info(self, obj):
        a = obj.asignacion
        if not a:
            return None
        return {
            "id": a.id,
            "direccion": a.direccion,
            "comuna": a.comuna,
            "fecha": a.fecha,
            "estado": a.estado,
            "asignado_a": a.asignado_a_id,
        }


class CsvRowResult(serializers.Serializer):
    rownum = serializers.IntegerField()
    created = serializers.BooleanField()
    updated = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField(), required=False)


# === NUEVO: serializer para el upload ===
class CargaCSVSerializer(serializers.Serializer):
    file = serializers.FileField()