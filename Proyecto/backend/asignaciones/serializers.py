from rest_framework import serializers
from .models import DireccionAsignada, HistorialAsignacion


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
    """
    Solo para que el navegador de DRF muestre un botón/form de POST.
    """
    confirm = serializers.BooleanField(required=False, default=True)


class EstadoClienteActionSerializer(serializers.Serializer):
    """
    Q5: sólo escoger la opción. Si elige 'Reagendó', la API redirige
    (303 See Other) a /estado_cliente/reagendar donde se exige fecha/bloque.
    """
    ESTADOS = [
        ("autoriza", "Autoriza a ingresar"),
        ("sin_moradores", "Sin Moradores"),
        ("rechaza", "Rechaza"),
        ("contingencia", "Contingencia externa"),
        ("masivo", "Incidencia Masivo ClaroVTR"),
        ("reagendo", "Reagendó"),
    ]
    estado_cliente = serializers.ChoiceField(choices=ESTADOS, write_only=True)


class ReagendarActionSerializer(serializers.Serializer):
    """
    Formulario dedicado a reagendamiento.
    """
    reagendado_fecha = serializers.DateField(help_text="YYYY-MM-DD (futuro)")
    reagendado_bloque = serializers.ChoiceField(
        choices=[("10-13", "10:00 a 13:00"), ("14-18", "14:00 a 18:00")]
    )
