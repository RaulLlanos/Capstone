# asignaciones/serializers.py
from rest_framework import serializers
from usuarios.models import Usuario
from .models import DireccionAsignada, HistorialAsignacion

# ---- Serializers base ----

class DireccionAsignadaSerializer(serializers.ModelSerializer):
    asignado_a = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(rol="tecnico"),
        required=False,
        allow_null=True
    )

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
        read_only_fields = ["created_at", "updated_at"]

    def get_fields(self):
        """
        Para técnicos:
          - estado: read-only (solo se cambia por /estado_cliente/)
          - reagendado_*: read-only (solo se cambia por /estado_cliente/ cuando es reagendo)
          - asignado_a: read-only (técnico no reasigna a otros)
        Admin mantiene edición completa.
        """
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or getattr(user, "rol", None) != "administrador":
            for name in ("estado", "reagendado_fecha", "reagendado_bloque", "asignado_a"):
                if name in fields:
                    fields[name].read_only = True
        return fields


class HistorialAsignacionSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(source="usuario.id", read_only=True)
    usuario_email = serializers.EmailField(source="usuario.email", read_only=True)
    asignacion_id = serializers.IntegerField(source="asignacion.id", read_only=True)
    asignacion_info = serializers.SerializerMethodField()

    # “Columnas” denormalizadas útiles para filtros/export
    marca = serializers.CharField(source="asignacion.marca", read_only=True)
    tecnologia = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    direccion = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    fecha = serializers.DateField(source="asignacion.fecha", read_only=True)
    bloque = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)

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
            "asignado_a": getattr(a.asignado_a, "id", None),
        }


# ---- Serializers para acciones de ViewSet (para que el UI de DRF muestre formularios) ----

class AsignarmeActionSerializer(serializers.Serializer):
    """
    No requiere campos, es solo para que el UI de DRF muestre un POST “bonito”.
    """
    pass


class EstadoClienteActionSerializer(serializers.Serializer):
    """
    Formulario Q5: opciones + validación condicional.
    """
    ESTADO_CHOICES = (
        ("autoriza", "Autoriza a ingresar"),
        ("sin_moradores", "Sin moradores"),
        ("rechaza", "Rechaza"),
        ("contingencia", "Contingencia externa"),
        ("masivo", "Incidencia Masivo ClaroVTR"),
        ("reagendo", "Reagendó"),
    )
    BLOQUE_CHOICES = (
        ("10-13", "10:00 a 13:00"),
        ("14-18", "14:00 a 18:00"),
    )

    estado_cliente = serializers.ChoiceField(choices=ESTADO_CHOICES)
    reagendado_fecha = serializers.DateField(required=False, allow_null=True)
    reagendado_bloque = serializers.ChoiceField(required=False, allow_null=True, choices=BLOQUE_CHOICES)

    def validate(self, attrs):
        if attrs.get("estado_cliente") == "reagendo":
            if not attrs.get("reagendado_fecha") or not attrs.get("reagendado_bloque"):
                raise serializers.ValidationError("Debe indicar fecha y bloque para reagendar.")
        return attrs


# ---- Serializers para carga de archivos (se usan en el endpoint cargar_csv) ----

class CsvRowResult(serializers.Serializer):
    rownum = serializers.IntegerField()
    created = serializers.BooleanField()
    updated = serializers.BooleanField()
    errors = serializers.ListField(child=serializers.CharField(), required=False)


class CargaCSVSerializer(serializers.Serializer):
    file = serializers.FileField()
