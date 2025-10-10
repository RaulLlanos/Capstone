# auditoria/serializers.py
from django.utils import timezone
from rest_framework import serializers

from .models import AuditoriaVisita
from asignaciones.models import HistorialAsignacion  # DireccionAsignada no se usa aquí

class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    # --- Campos derivados de la asignación (solo lectura) ---
    marca = serializers.CharField(source="asignacion.marca", read_only=True)
    tecnologia = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    direccion = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    fecha = serializers.DateField(source="asignacion.fecha", read_only=True)
    bloque = serializers.CharField(source="asignacion.bloque", read_only=True)
    tecnico_id = serializers.IntegerField(source="asignacion.asignado_a", read_only=True)

    class Meta:
        model = AuditoriaVisita
        fields = [
            # originales (editables según tu flujo)
            "id", "asignacion", "tecnico",
            "estado_cliente",
            "reagendado_fecha", "reagendado_bloque",
            "ont_modem_ok",
            "servicios", "categorias", "descripcion_problema", "fotos",
            "bloque_agendamiento", "bloque_llegada", "bloque_proceso",
            "bloque_config", "bloque_cierre", "percepcion",
            "created_at",

            # agregados (solo lectura desde la asignación)
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]
        read_only_fields = [
            "id", "created_at", "tecnico",
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]

    def validate(self, attrs):
        estado = attrs.get("estado_cliente") or getattr(self.instance, "estado_cliente", None)

        # Si reagenda, requiere fecha futura y bloque
        if estado == "reagendo":
            f = attrs.get("reagendado_fecha")
            b = attrs.get("reagendado_bloque")
            if not f or not b:
                raise serializers.ValidationError("Debe indicar fecha y bloque de reagendamiento.")
            if f < timezone.localdate():
                raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        u = getattr(request, "user", None)

        asignacion = validated_data["asignacion"]
        # setea técnico que crea la auditoría (si es técnico)
        validated_data["tecnico"] = u if u and getattr(u, "rol", None) == "tecnico" else None

        audit = super().create(validated_data)

        # --- Efectos colaterales sobre la asignación (estado_cliente) + historial ---
        if audit.estado_cliente == "reagendo":
            asignacion.reagendado_fecha = audit.reagendado_fecha
            asignacion.reagendado_bloque = audit.reagendado_bloque
            asignacion.estado = "REAGENDADA"
            asignacion.save()
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion="reagendada",
                detalles=f"Reagendada desde auditoría a {audit.reagendado_fecha} {audit.reagendado_bloque}",
                usuario=u,
            )
        elif audit.estado_cliente == "autoriza":
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion="auditoria_creada",
                detalles="Auditoría con estado 'autoriza'.",
                usuario=u,
            )
        else:
            # sin_moradores / rechaza / contingencia / masivo
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion="estado_cambiado",
                detalles=f"Auditoría 'estado_cliente'={audit.estado_cliente}.",
                usuario=u,
            )

        return audit
