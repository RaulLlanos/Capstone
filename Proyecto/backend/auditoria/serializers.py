from django.utils import timezone
from rest_framework import serializers
from .models import AuditoriaVisita


class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    # ---- Derivados de la asignación (solo lectura, no rompen el contrato) ----
    marca = serializers.CharField(source="asignacion.marca", read_only=True)
    tecnologia = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    direccion = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    fecha = serializers.DateField(source="asignacion.fecha", read_only=True)
    bloque = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)
    tecnico_id = serializers.IntegerField(source="asignacion.asignado_a_id", read_only=True)

    class Meta:
        model = AuditoriaVisita
        fields = [
            "id", "created_at",
            "asignacion", "tecnico", "customer_status",

            # Reagenda
            "reschedule_date", "reschedule_slot",

            # Diagnóstico / servicios
            "ont_modem_ok", "service_issues",
            "internet_categoria", "internet_otro",
            "tv_categoria", "tv_otro",
            "otro_descripcion",

            # Evidencias
            "photo1", "photo2", "photo3",

            # Solo HFC
            "desc_hfc",

            # Agendamiento
            "schedule_informed_datetime",
            "schedule_informed_adult_required",
            "schedule_informed_services",
            "agend_comentarios",

            # Llegada
            "arrival_within_slot",
            "identification_shown",
            "explained_before_start",
            "llegada_comentarios",

            # Proceso instalación
            "asked_equipment_location",
            "tidy_and_safe_install",
            "tidy_cabling",
            "verified_signal_levels",
            "proceso_comentarios",

            # Configuración y pruebas
            "configured_router",
            "tested_device",
            "tv_functioning",
            "left_instructions",
            "config_comentarios",

            # Cierre
            "reviewed_with_client",
            "got_consent_signature",
            "left_contact_info",
            "cierre_comentarios",

            # Percepción / NPS
            "percepcion", "nps_proceso", "nps_tecnico", "nps_claro_vtr",

            # Solución / gestión / info
            "solucion_gestion", "orden_tipo", "info_tipo",
            "detalle_mala_practica_empresa", "detalle_mala_practica_instalador",

            # Final
            "descripcion_problema",

            # Derivados (solo lectura)
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]
        read_only_fields = [
            "id", "created_at", "tecnico",
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]

    # -------- Validaciones de negocio --------
    def validate(self, attrs):
        status_val = attrs.get("customer_status") or getattr(self.instance, "customer_status", None)
        if status_val == "REAGENDA":
            f = attrs.get("reschedule_date") or getattr(self.instance, "reschedule_date", None)
            b = attrs.get("reschedule_slot") or getattr(self.instance, "reschedule_slot", "")
            if not f or not b:
                raise serializers.ValidationError("Debe indicar fecha y bloque de reagendamiento.")
            if f < timezone.localdate():
                raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        u = getattr(request, "user", None)
        if u and getattr(u, "rol", None) == "tecnico":
            asignacion = validated_data["asignacion"]
            if asignacion.asignado_a_id != u.id:
                raise serializers.ValidationError("Solo puedes auditar tus asignaciones.")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
