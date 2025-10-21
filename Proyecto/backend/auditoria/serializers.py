from django.utils import timezone
from rest_framework import serializers

from .models import (
    AuditoriaVisita, Tri, EstadoCliente,
    SERVICIO_CHOICES, INTERNET_CAT_CHOICES, TV_CAT_CHOICES,
)
from asignaciones.models import DireccionAsignada


class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    # Derivados (solo lectura) desde la asignación
    brand = serializers.CharField(source="asignacion.marca", read_only=True)
    technology = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    address = serializers.CharField(source="asignacion.direccion", read_only=True)
    commune = serializers.CharField(source="asignacion.comuna", read_only=True)
    scheduled_date = serializers.DateField(source="asignacion.fecha", read_only=True)
    scheduled_block = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)
    assigned_tech_id = serializers.IntegerField(source="asignacion.asignado_a_id", read_only=True)

    # Normalizamos que 'services' siempre sea lista de strings
    services = serializers.ListField(
        child=serializers.ChoiceField(choices=[c[0] for c in SERVICIO_CHOICES]),
        allow_empty=True, required=False
    )

    class Meta:
        model = AuditoriaVisita
        fields = [
            "id", "created_at",

            # Identificación
            "asignacion", "tecnico",  # 'tecnico' se setea automáticamente para técnicos
            "customer_status",

            # Reagendamiento observado en auditoría (no toca la asignación)
            "reschedule_date", "reschedule_block",

            # Estado/equipo
            "ont_modem_ok",

            # Problemas por servicio
            "services",
            "internet_issue_category", "internet_issue_other",
            "tv_issue_category", "tv_issue_other",
            "other_issue_description",

            # Evidencias
            "photo1", "photo2", "photo3",

            # Solo HFC
            "hfc_problem_description",

            # AGENDAMIENTO
            "schedule_informed_datetime",
            "schedule_informed_adult_required",
            "schedule_informed_services",
            "schedule_comments",

            # Llegada
            "arrival_within_slot", "identification_shown", "explained_before_start",
            "arrival_comments",

            # Proceso
            "asked_equipment_location", "tidy_and_safe_install", "tidy_cabling",
            "verified_signal_levels", "install_process_comments",

            # Config/pruebas
            "configured_router", "tested_device", "tv_functioning", "left_instructions",
            "config_comments",

            # Cierre
            "reviewed_with_client", "got_consent_signature", "left_contact_info",
            "closure_comments",

            # Percepción / NPS
            "perception_notes", "nps_process", "nps_technician", "nps_brand",

            # Resolución / Gestión / Mala práctica
            "resolution", "order_type", "info_type",
            "malpractice_company_detail", "malpractice_installer_detail",

            # Finalizar
            "final_problem_description",

            # Derivados (lectura)
            "brand", "technology", "address", "commune",
            "scheduled_date", "scheduled_block", "assigned_tech_id",
        ]
        read_only_fields = [
            "id", "created_at", "tecnico",
            "brand", "technology", "address", "commune",
            "scheduled_date", "scheduled_block", "assigned_tech_id",
        ]

    # --- Validaciones condicionales (reflejan .clean() del modelo) ---
    def validate(self, attrs):
        # Normaliza services a lista
        services = attrs.get("services")
        if services is None:
            # si no viene en payload, no lo toques (para PATCH)
            if self.instance is None:
                attrs["services"] = []
        # Reglas por servicio
        final_services = (attrs.get("services")
                          if attrs.get("services") is not None
                          else (self.instance.services if self.instance else []))
        sset = set(final_services or [])

        # Internet -> requiere categoría; si 'otro', requiere texto
        internet_cat = attrs.get("internet_issue_category",
                                 getattr(self.instance, "internet_issue_category", ""))
        internet_otro = attrs.get("internet_issue_other",
                                  getattr(self.instance, "internet_issue_other", ""))
        if "internet" in sset and not internet_cat:
            raise serializers.ValidationError("Si marcaste 'Internet' debes elegir 'Categoría problema Internet'.")
        if internet_cat == "otro" and not (internet_otro or "").strip():
            raise serializers.ValidationError("Describe el 'Otro' de Internet.")

        # TV -> requiere categoría; si 'otro', requiere texto
        tv_cat = attrs.get("tv_issue_category",
                           getattr(self.instance, "tv_issue_category", ""))
        tv_otro = attrs.get("tv_issue_other",
                            getattr(self.instance, "tv_issue_other", ""))
        if "tv" in sset and not tv_cat:
            raise serializers.ValidationError("Si marcaste 'TV' debes elegir 'Categoría problema TV'.")
        if tv_cat == "otro" and not (tv_otro or "").strip():
            raise serializers.ValidationError("Describe el 'Otro' de TV.")

        # 'otro' en services -> exige descripción
        otro_desc = attrs.get("other_issue_description",
                              getattr(self.instance, "other_issue_description", "")) or ""
        if "otro" in sset and not otro_desc.strip():
            raise serializers.ValidationError("Describe el problema 'Otro'.")

        # Si customer_status = REAGENDA y vienen campos, valida fecha/bloque (solo a nivel de auditoría)
        cs = attrs.get("customer_status", getattr(self.instance, "customer_status", ""))
        if cs == EstadoCliente.REAGENDA:
            f = attrs.get("reschedule_date", getattr(self.instance, "reschedule_date", None))
            b = attrs.get("reschedule_block", getattr(self.instance, "reschedule_block", ""))
            if (f and f < timezone.localdate()):
                raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
            if b and b not in {"10-13", "14-18"}:
                raise serializers.ValidationError("Bloque inválido (use 10-13 o 14-18).")

        return attrs

    # --- Create / Update ---
    def create(self, validated_data):
        request = self.context.get("request")
        u = getattr(request, "user", None)

        asignacion = validated_data["asignacion"]
        # Si es técnico: debe ser su asignación
        if getattr(u, "rol", None) == "tecnico":
            if getattr(asignacion, "asignado_a_id", None) != getattr(u, "id", None):
                raise serializers.ValidationError("Solo puedes auditar asignaciones que te pertenecen.")
            validated_data["tecnico"] = u  # guardamos quién creó

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        u = getattr(request, "user", None)

        # Si es técnico, no permitimos cambiar la asignación ni mover la auditoría a otra persona
        if getattr(u, "rol", None) == "tecnico":
            if "asignacion" in validated_data and validated_data["asignacion"].id != instance.asignacion_id:
                raise serializers.ValidationError("No puedes cambiar la asignación de la auditoría.")
            validated_data["tecnico"] = instance.tecnico or u

        return super().update(instance, validated_data)
