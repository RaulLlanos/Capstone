from django.utils import timezone
from rest_framework import serializers

from .models import AuditoriaVisita
from asignaciones.models import HistorialAsignacion

class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    # Derivados desde la asignación
    marca = serializers.CharField(source="asignacion.marca", read_only=True)
    tecnologia = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    direccion = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    fecha = serializers.DateField(source="asignacion.fecha", read_only=True)
    bloque = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)
    tecnico_id = serializers.IntegerField(source="asignacion.asignado_a_id", read_only=True)  # FIX

    class Meta:
        model = AuditoriaVisita
        fields = [
            "id", "asignacion", "tecnico",
            "estado_cliente",
            "reagendado_fecha", "reagendado_bloque",
            "ont_modem_ok",
            "servicios", "categorias", "descripcion_problema", "fotos",
            "bloque_agendamiento", "bloque_llegada", "bloque_proceso",
            "bloque_config", "bloque_cierre", "percepcion",
            "created_at",
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]
        read_only_fields = [
            "id", "created_at", "tecnico",
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]

    def validate(self, attrs):
        estado = attrs.get("estado_cliente") or getattr(self.instance, "estado_cliente", None)
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
        validated_data["tecnico"] = u if u and getattr(u, "rol", None) == "tecnico" else None

        audit = super().create(validated_data)

        if audit.estado_cliente == "reagendo":
            asignacion.reagendado_fecha = audit.reagendado_fecha
            asignacion.reagendado_bloque = audit.reagendado_bloque
            asignacion.estado = "REAGENDADA"
            asignacion.save()
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion="REAGENDADA",
                detalles=f"Reagendada desde auditoría a {audit.reagendado_fecha} {audit.reagendado_bloque}",
                usuario=u,
            )
        elif audit.estado_cliente == "autoriza":
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion="CERRADA",
                detalles="Auditoría con estado 'autoriza'. Marcada VISITADA.",
                usuario=u,
            )
        else:
            HistorialAsignacion.objects.create(
                asignacion=asignacion,
                accion="ESTADO_CLIENTE",
                detalles=f"Auditoría 'estado_cliente'={audit.estado_cliente}.",
                usuario=u,
            )

        return audit
