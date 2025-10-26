from rest_framework import serializers
from .models import DireccionAsignada, HistorialAsignacion
from django.utils import timezone


# === Serializadores base ===

class DireccionAsignadaSerializer(serializers.ModelSerializer):
    """
    Serializa una asignación tal como se muestra en tus respuestas actuales.
    """
    asignado_a = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DireccionAsignada
        fields = [
            "id",
            "fecha",
            "tecnologia",
            "marca",
            "rut_cliente",
            "id_vivienda",
            "direccion",
            "comuna",
            "zona",
            "encuesta",
            "id_qualtrics",
            "estado",
            "reagendado_fecha",
            "reagendado_bloque",
            "created_at",
            "updated_at",
            "asignado_a",
        ]
        read_only_fields = [
            "created_at", "updated_at", "asignado_a",
        ]


class HistorialAsignacionSerializer(serializers.ModelSerializer):
    """
    Historial con campos de apoyo para el listado/exports.
    """
    usuario_id = serializers.IntegerField(source="usuario.id", read_only=True)
    usuario_email = serializers.EmailField(source="usuario.email", read_only=True)
    asignacion_id = serializers.IntegerField(source="asignacion.id", read_only=True)

    asignacion_info = serializers.SerializerMethodField()
    marca = serializers.CharField(source="asignacion.marca", read_only=True)
    tecnologia = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    direccion = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    fecha = serializers.DateField(source="asignacion.fecha", read_only=True)
    bloque = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)

    def get_asignacion_info(self, obj):
        a = obj.asignacion
        if not a:
            return None
        return {
            "id": a.id,
            "direccion": a.direccion,
            "comuna": a.comuna,
            "fecha": a.fecha.isoformat() if a.fecha else None,
            "estado": a.estado,
            "asignado_a": a.asignado_a_id,
        }

    class Meta:
        model = HistorialAsignacion
        fields = [
            "id",
            "accion",
            "detalles",
            "created_at",
            "usuario_id",
            "usuario_email",
            "asignacion_id",
            "asignacion_info",
            "marca",
            "tecnologia",
            "direccion",
            "comuna",
            "fecha",
            "bloque",
        ]


# === Apoyo para carga CSV/XLSX (interfaz de OpenAPI) ===

class CsvRowResult(serializers.Serializer):
    rownum = serializers.IntegerField()
    created = serializers.BooleanField()
    updated = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField(), required=False)


class CargaCSVSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="Archivo .csv o .xlsx")


# === Acciones (formularios simples para el navegador de DRF) ===

class AsignarmeActionSerializer(serializers.Serializer):
    para_hoy = serializers.BooleanField(required=False, default=False)
    bloque = serializers.CharField(required=False, allow_blank=True)


class EstadoClienteActionSerializer(serializers.Serializer):
    """
    Serializer para la acción Q5 /estado_cliente/.
    Solo escritura (write_only) para que el GET no intente serializar el modelo.
    """
    ESTADOS_Q5 = [
        ("autoriza", "Autoriza a ingresar"),
        ("sin_moradores", "Sin Moradores"),
        ("rechaza", "Rechaza"),
        ("contingencia", "Contingencia externa"),
        ("masivo", "Incidencia Masivo ClaroVTR"),
        ("reagendo", "Reagendó"),
    ]

    estado_cliente = serializers.ChoiceField(
        choices=ESTADOS_Q5, write_only=True,
        help_text="Seleccione el resultado de la visita (Q5)."
    )
    reagendado_fecha = serializers.DateField(
        required=False, write_only=True,
        input_formats=["%Y-%m-%d"],
        help_text="Requerido si 'Reagendó'. Formato YYYY-MM-DD."
    )
    reagendado_bloque = serializers.ChoiceField(
        required=False, write_only=True,
        choices=[("10-13", "10:00 a 13:00"), ("14-18", "14:00 a 18:00")],
        help_text="Requerido si 'Reagendó'."
    )
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate(self, attrs):
        estado = attrs.get("estado_cliente")
        if estado == "reagendo":
            f = attrs.get("reagendado_fecha")
            b = attrs.get("reagendado_bloque")
            if not f or not b:
                raise serializers.ValidationError("Debe indicar fecha y bloque de reagendamiento.")
            # fecha no pasada
            if f < timezone.localdate():
                raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
        return attrs


class ReagendarActionSerializer(serializers.Serializer):
    fecha = serializers.DateField(
        write_only=True,
        input_formats=["%Y-%m-%d"],
        help_text="Nueva fecha (YYYY-MM-DD, ≥ hoy).",
    )
    # ChoiceField => DRF renderiza <select>
    bloque = serializers.ChoiceField(
        write_only=True,
        choices=[("10-13", "10:00 a 13:00"), ("14-18", "14:00 a 18:00")],
        help_text="Selecciona el bloque.",
    )
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=200)

    def validate_fecha(self, val):
        if str(val) < str(timezone.localdate()):
            raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
        return val