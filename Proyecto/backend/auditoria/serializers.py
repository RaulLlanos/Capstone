from rest_framework import serializers
from .models import Auditoria, AuditoriaServicio, AuditoriaCategoria, EvidenciaServicio
from asignaciones.models import Asignacion, EstadoAsignacion, HistorialAsignacion

class AuditoriaCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditoriaCategoria
        fields = ("id", "categoria", "extra")

class AuditoriaServicioSerializer(serializers.ModelSerializer):
    categorias = AuditoriaCategoriaSerializer(many=True, required=False)

    class Meta:
        model = AuditoriaServicio
        fields = ("id", "servicio", "categorias")

class AuditoriaSerializer(serializers.ModelSerializer):
    servicios = AuditoriaServicioSerializer(many=True, required=False)

    class Meta:
        model = Auditoria
        fields = (
            "id", "asignacion",
            "marca","tecnologia","rut_cliente","id_vivienda","direccion_cliente",
            "estado_cliente","ont_modem_ok",
            "bloque_agendamiento","bloque_llegada","bloque_proceso","bloque_config","bloque_cierre","percepcion",
            "descripcion_problema",
            "servicios",
            "created_at",
        )
        read_only_fields = ("marca","tecnologia","rut_cliente","id_vivienda","direccion_cliente","created_at")

    def validate(self, attrs):
        request = self.context.get("request")
        asignacion = attrs.get("asignacion")
        if not asignacion:
            raise serializers.ValidationError("Falta asignación.")

        # Técnicos: solo su propia asignación
        if request and getattr(request.user, "rol", None) == "tecnico":
            if asignacion.asignado_a_id != request.user.id:
                raise serializers.ValidationError("No autorizado para esta asignación.")

        return attrs

    def create(self, validated_data):
        servicios_data = validated_data.pop("servicios", [])
        asignacion: Asignacion = validated_data["asignacion"]

        # Snapshot desde Asignacion/Direccion al momento de crear
        auditoria = Auditoria.objects.create(
            asignacion = asignacion,
            estado_cliente = validated_data.get("estado_cliente"),
            ont_modem_ok   = validated_data.get("ont_modem_ok"),
            bloque_agendamiento = validated_data.get("bloque_agendamiento"),
            bloque_llegada      = validated_data.get("bloque_llegada"),
            bloque_proceso      = validated_data.get("bloque_proceso"),
            bloque_config       = validated_data.get("bloque_config"),
            bloque_cierre       = validated_data.get("bloque_cierre"),
            percepcion          = validated_data.get("percepcion"),
            descripcion_problema = validated_data.get("descripcion_problema"),
            marca = asignacion.marca,
            tecnologia = asignacion.tecnologia,
            rut_cliente = asignacion.rut_cliente,
            id_vivienda = asignacion.id_vivienda,
            direccion_cliente = asignacion.direccion,
        )

        # Servicios/categorías anidados (opcionales)
        for s in servicios_data:
            cats = s.pop("categorias", [])
            serv = AuditoriaServicio.objects.create(auditoria=auditoria, **s)
            for c in cats:
                AuditoriaCategoria.objects.create(auditoria_servicio=serv, **c)

        # Trazabilidad: marcar VISITADA (por si no lo estaba) y guardar historial
        if asignacion.estado != EstadoAsignacion.VISITADA:
            asignacion.estado = EstadoAsignacion.VISITADA
            asignacion.save(update_fields=["estado"])
        HistorialAsignacion.objects.create(
            asignacion=asignacion,
            accion=HistorialAsignacion.Accion.AUDITORIA_CREADA,
            detalles=f"Auditoría {auditoria.id} creada",
            usuario=self.context.get("request").user if self.context.get("request") else None
        )

        return auditoria

class EvidenciaServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaServicio
        fields = ("id","auditoria","asignacion","tipo","archivo","descripcion","usuario","created_at")
        read_only_fields = ("usuario","created_at")
