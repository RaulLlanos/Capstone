from django.utils import timezone
from rest_framework import serializers

from .models import AuditoriaVisita

# Conjuntos permitidos (sin depender de constantes del modelo)
SERVICE_ALLOWED = ("internet", "tv", "fono", "otro")
BLOCK_ALLOWED = ("10-13", "14-18")


class AuditoriaVisitaSerializer(serializers.ModelSerializer):
    # Derivados desde la asignación (solo lectura)
    brand = serializers.CharField(source="asignacion.marca", read_only=True)
    technology = serializers.CharField(source="asignacion.tecnologia", read_only=True)
    address = serializers.CharField(source="asignacion.direccion", read_only=True)
    comuna = serializers.CharField(source="asignacion.comuna", read_only=True)
    date = serializers.DateField(source="asignacion.fecha", read_only=True)
    block = serializers.CharField(source="asignacion.reagendado_bloque", read_only=True)
    tecnico_id = serializers.IntegerField(source="asignacion.asignado_a_id", read_only=True)

    # Lista JSON de servicios con problema (checkboxes)
    services = serializers.ListField(
        child=serializers.ChoiceField(choices=SERVICE_ALLOWED),
        required=False
    )

    class Meta:
        model = AuditoriaVisita
        fields = [
            "id", "asignacion", "tecnico",

            # Estado observado por el auditor
            "customer_status",
            "reschedule_date", "reschedule_block",

            # ONT / módem
            "ont_modem_ok",

            # Problemas/servicios
            "services",
            "internet_issue_category", "internet_issue_other",
            "tv_issue_category", "tv_issue_other",
            "other_issue_description",

            # Evidencias (3 fotos)
            "photo1", "photo2", "photo3",

            # Solo HFC
            "hfc_problem_description",

            # Agendamiento
            "schedule_informed_datetime",
            "schedule_informed_adult_required",
            "schedule_informed_services",
            "schedule_comments",

            # Llegada
            "arrival_within_slot",
            "identification_shown",
            "explained_before_start",
            "arrival_comments",

            # Proceso instalación
            "asked_equipment_location",
            "tidy_and_safe_install",
            "tidy_cabling",
            "verified_signal_levels",
            "install_process_comments",

            # Configuración y pruebas
            "configured_router",
            "tested_device",
            "tv_functioning",
            "left_instructions",
            "config_comments",

            # Cierre
            "reviewed_with_client",
            "got_consent_signature",
            "left_contact_info",
            "closure_comments",

            # Percepción / NPS
            "perception_notes",
            "nps_process", "nps_technician", "nps_brand",

            # Solución / Gestión / Mala práctica
            "resolution",
            "order_type",
            "info_type",
            "malpractice_company_detail",
            "malpractice_installer_detail",

            # Final
            "final_problem_description",

            # Metadatos
            "created_at",

            # Derivados (read-only)
            "brand", "technology", "address", "comuna", "date", "block", "tecnico_id",
        ]
        read_only_fields = [
            "id", "created_at", "tecnico",
            "brand", "technology", "address", "comuna", "date", "block", "tecnico_id",
        ]

    def _normalize_customer_status(self, raw):
        if raw is None:
            return None
        m = {
            "1": "AUTORIZA",
            "2": "SIN_MORADORES",
            "3": "RECHAZA",
            "4": "CONTINGENCIA",
            "5": "MASIVO",
            "6": "REAGENDA",
            "autoriza": "AUTORIZA",
            "sin_moradores": "SIN_MORADORES",
            "rechaza": "RECHAZA",
            "contingencia": "CONTINGENCIA",
            "masivo": "MASIVO",
            "reagendo": "REAGENDA",
            "reagenda": "REAGENDA",
        }
        key = str(raw).strip().lower()
        return m.get(key, str(raw).upper())

    def validate(self, attrs):
        # Normaliza estado
        if "customer_status" in attrs:
            attrs["customer_status"] = self._normalize_customer_status(attrs["customer_status"])
        else:
            # Mantiene el existente si está en update
            if self.instance and self.instance.customer_status:
                attrs["customer_status"] = self.instance.customer_status

        # Si marcó REAGENDA en la auditoría, exige fecha y bloque válidos (esto NO cambia la asignación)
        if attrs.get("customer_status") == "REAGENDA":
            f = attrs.get("reschedule_date") or (self.instance and self.instance.reschedule_date)
            b = attrs.get("reschedule_block") or (self.instance and self.instance.reschedule_block)
            if not f or not b:
                raise serializers.ValidationError("Debe indicar reschedule_date y reschedule_block.")
            if f < timezone.localdate():
                raise serializers.ValidationError("La fecha reagendada no puede ser pasada.")
            if b not in BLOCK_ALLOWED:
                raise serializers.ValidationError("Bloque inválido (use 10-13 o 14-18).")

        # Validaciones condicionales de servicios/categorías
        services = set(attrs.get("services")
                       or (self.instance and self.instance.services)
                       or [])

        internet_cat = attrs.get("internet_issue_category") or (self.instance and self.instance.internet_issue_category)
        if "internet" in services and not internet_cat:
            raise serializers.ValidationError("Si marcaste Internet, debes elegir 'Internet issue category'.")
        if (internet_cat == "otro") and not (attrs.get("internet_issue_other")
                                             or (self.instance and self.instance.internet_issue_other)):
            raise serializers.ValidationError("Describe el 'Otro' de Internet.")

        tv_cat = attrs.get("tv_issue_category") or (self.instance and self.instance.tv_issue_category)
        if "tv" in services and not tv_cat:
            raise serializers.ValidationError("Si marcaste TV, debes elegir 'TV issue category'.")
        if (tv_cat == "otro") and not (attrs.get("tv_issue_other")
                                       or (self.instance and self.instance.tv_issue_other)):
            raise serializers.ValidationError("Describe el 'Otro' de TV.")

        if "otro" in services and not (attrs.get("other_issue_description")
                                       or (self.instance and self.instance.other_issue_description)):
            raise serializers.ValidationError("Describe el problema en 'Other issue description'.")

        return attrs

    def create(self, validated_data):
        """
        - Si el usuario es técnico: fuerza tecnico=request.user y verifica que la asignación le pertenezca.
        - NO toca el estado/fechas de la asignación (eso se hace en /api/asignaciones/...).
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        asignacion = validated_data["asignacion"]

        if user and getattr(user, "rol", None) == "tecnico":
            if asignacion.asignado_a_id != user.id:
                raise serializers.ValidationError("No puedes auditar una asignación que no te pertenece.")
            validated_data["tecnico"] = user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        - Si el usuario es técnico: no permitir cambiar 'asignacion' ni 'tecnico'.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and getattr(user, "rol", None) == "tecnico":
            validated_data.pop("asignacion", None)
            validated_data.pop("tecnico", None)
        return super().update(instance, validated_data)
