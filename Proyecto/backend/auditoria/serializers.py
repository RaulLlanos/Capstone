from django.utils import timezone
from rest_framework import serializers
from .models import AuditoriaVisita

class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    # Derivados de la asignación (solo lectura)
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
            "reschedule_date", "reschedule_slot",
            "ont_modem_ok",
            # Problema/servicios
            "service_issues", "internet_issue_category", "internet_issue_other",
            "tv_issue_category", "tv_issue_other", "other_issue_description",
            # Evidencias
            "photo1", "photo2", "photo3",
            # Solo HFC
            "hfc_problem_description",
            # AGENDAMIENTO
            "schedule_informed_datetime", "schedule_informed_adult_required",
            "schedule_informed_services", "schedule_comments",
            # Llegada
            "arrival_within_slot", "identification_shown", "explained_before_start", "arrival_comments",
            # Proceso instalación
            "asked_equipment_location", "tidy_and_safe_install", "tidy_cabling",
            "verified_signal_levels", "install_process_comments",
            # Configuración y pruebas
            "configured_router", "tested_device", "tv_functioning",
            "left_instructions", "config_comments",
            # Cierre
            "reviewed_with_client", "got_consent_signature", "left_contact_info", "closure_comments",
            # Percepción / NPS
            "perception_notes", "nps_process", "nps_technician", "nps_brand",
            # Gestión
            "resolution", "order_type", "info_type",
            "malpractice_company_detail", "malpractice_installer_detail",
            # Final
            "final_problem_description",
            # Derivados de asignación
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]
        read_only_fields = [
            "id", "created_at", "tecnico",
            "marca", "tecnologia", "direccion", "comuna", "fecha", "bloque", "tecnico_id",
        ]

    def validate(self, attrs):
        # Si es REAGENDA, exige fecha/bloque válidos y no pasados
        status = attrs.get("customer_status") or getattr(self.instance, "customer_status", None)
        if status == "REAGENDA":
            f = attrs.get("reschedule_date") or getattr(self.instance, "reschedule_date", None)
            b = attrs.get("reschedule_slot") or getattr(self.instance, "reschedule_slot", "")
            if not f or not b:
                raise serializers.ValidationError("Debe indicar fecha y bloque de reagendamiento.")
            if f < timezone.localdate():
                raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
        return attrs

    def create(self, validated_data):
        """
        - Si la crea un técnico, se asocia automáticamente a `tecnico`.
        - Los efectos colaterales (reagendo / historial) los maneja signals.py
        """
        request = self.context.get("request")
        u = getattr(request, "user", None)
        if u and getattr(u, "rol", None) == "tecnico":
            validated_data["tecnico"] = u
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Permite edición; los side-effects sólo los disparamos en creación (signals)
        return super().update(instance, validated_data)
