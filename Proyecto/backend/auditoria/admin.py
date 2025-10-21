# auditoria/admin.py
from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AuditoriaVisita,
    Tri,
    EstadoCliente,
    SERVICIO_CHOICES,
)

# -----------------------------
# Form con widgets adecuados
# -----------------------------
class AuditoriaVisitaForm(forms.ModelForm):
    # JSONField -> checkboxes múltiples (Q8: servicios con problema)
    service_issues = forms.MultipleChoiceField(
        choices=SERVICIO_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = AuditoriaVisita
        exclude = ()
        widgets = {
            # Radios para todos los campos Tri
            "ont_modem_ok": forms.RadioSelect,
            "schedule_informed_datetime": forms.RadioSelect,
            "schedule_informed_adult_required": forms.RadioSelect,
            "schedule_informed_services": forms.RadioSelect,
            "arrival_within_slot": forms.RadioSelect,
            "identification_shown": forms.RadioSelect,
            "explained_before_start": forms.RadioSelect,
            "asked_equipment_location": forms.RadioSelect,
            "tidy_and_safe_install": forms.RadioSelect,
            "tidy_cabling": forms.RadioSelect,
            "verified_signal_levels": forms.RadioSelect,
            "configured_router": forms.RadioSelect,
            "tested_device": forms.RadioSelect,
            "tv_functioning": forms.RadioSelect,
            "left_instructions": forms.RadioSelect,
            "reviewed_with_client": forms.RadioSelect,
            "got_consent_signature": forms.RadioSelect,
            "left_contact_info": forms.RadioSelect,

            # Selects para campos con choices
            "customer_status": forms.Select,
            "internet_issue_category": forms.Select,
            "tv_issue_category": forms.Select,
            "resolution": forms.Select,
            "order_type": forms.Select,
            "info_type": forms.Select,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializa checkboxes desde JSON list del modelo
        if self.instance and self.instance.pk and isinstance(self.instance.service_issues, list):
            self.fields["service_issues"].initial = self.instance.service_issues

        # Ayudas
        if "reschedule_slot" in self.fields:
            self.fields["reschedule_slot"].help_text = "Usar 10-13 o 14-18"

        for nps_field in ("nps_process", "nps_technician", "nps_brand"):
            if nps_field in self.fields:
                self.fields[nps_field].help_text = "Rango 0 a 10"

    def clean(self):
        cleaned = super().clean()
        # Persistir service_issues (lista) al JSONField del modelo
        servicios = cleaned.get("service_issues") or []
        self.instance.service_issues = list(servicios)
        return cleaned


# -----------------------------
# Admin
# -----------------------------
@admin.register(AuditoriaVisita)
class AuditoriaVisitaAdmin(admin.ModelAdmin):
    form = AuditoriaVisitaForm

    list_display = (
        "id",
        "asignacion_str",
        "customer_status",
        "ont_modem_ok",
        "services_str",
        "tecnico",
        "created_at",
        "photo1_thumb",
        "photo2_thumb",
        "photo3_thumb",
    )
    list_filter = (
        "customer_status",
        "ont_modem_ok",
        "resolution",
        "info_type",
        ("created_at", admin.DateFieldListFilter),
    )
    search_fields = ("asignacion__direccion", "asignacion__comuna", "tecnico__email")
    readonly_fields = ("created_at", "photo1_thumb", "photo2_thumb", "photo3_thumb")

    fieldsets = (
        ("Identificación", {
            "fields": ("asignacion", "tecnico", "customer_status")
        }),
        ("Reagendamiento (si aplica)", {
            "classes": ("collapse",),
            "fields": ("reschedule_date", "reschedule_slot")
        }),
        ("Estado y equipos", {
            "fields": ("ont_modem_ok",)
        }),
        ("Servicio con problema (equiv. Q8–Q11)", {
            "fields": (
                "service_issues",
                ("internet_issue_category", "internet_issue_other"),
                ("tv_issue_category", "tv_issue_other"),
                "other_issue_description",
            )
        }),
        ("Evidencias (fotos)", {
            "fields": ("photo1", "photo2", "photo3")
        }),
        ("Solo HFC (descripción problema)", {
            "classes": ("collapse",),
            "fields": ("hfc_problem_description",)
        }),
        ("AGENDAMIENTO", {
            "fields": (
                ("schedule_informed_datetime", "schedule_informed_adult_required", "schedule_informed_services"),
                "schedule_comments",
            )
        }),
        ("Llegada del técnico", {
            "fields": (
                ("arrival_within_slot", "identification_shown", "explained_before_start"),
                "arrival_comments",
            )
        }),
        ("Proceso de instalación", {
            "fields": (
                ("asked_equipment_location", "tidy_and_safe_install", "tidy_cabling", "verified_signal_levels"),
                "install_process_comments",
            )
        }),
        ("Configuración y pruebas", {
            "fields": (
                ("configured_router", "tested_device", "tv_functioning", "left_instructions"),
                "config_comments",
            )
        }),
        ("Cierre de visita técnica", {
            "fields": (
                ("reviewed_with_client", "got_consent_signature", "left_contact_info"),
                "closure_comments",
            )
        }),
        ("Percepción del cliente / NPS", {
            "fields": ("perception_notes", "nps_process", "nps_technician", "nps_brand")
        }),
        ("Solución / Gestión / Mala práctica", {
            "fields": (
                "resolution", "order_type",
                "info_type", "malpractice_company_detail", "malpractice_installer_detail",
            )
        }),
        ("Finalizar", {
            "fields": ("final_problem_description",)
        }),
        ("Metadatos", {
            "classes": ("collapse",),
            "fields": ("created_at", "photo1_thumb", "photo2_thumb", "photo3_thumb")
        }),
    )

    # Helpers de visualización
    def asignacion_str(self, obj):
        a = obj.asignacion
        return f"{a.direccion} ({a.comuna})" if a else "-"
    asignacion_str.short_description = "Dirección"

    def services_str(self, obj):
        vals = obj.service_issues or []
        if not vals:
            return "-"
        label_by_val = dict(SERVICIO_CHOICES)
        return ", ".join(label_by_val.get(v, v) for v in vals)
    services_str.short_description = "Servicios"

    # Thumbnails de fotos (solo lectura)
    def _thumb(self, filefield):
        if not filefield:
            return "-"
        return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', filefield.url)

    def photo1_thumb(self, obj): return self._thumb(obj.photo1)
    def photo2_thumb(self, obj): return self._thumb(obj.photo2)
    def photo3_thumb(self, obj): return self._thumb(obj.photo3)

    photo1_thumb.short_description = "Foto 1"
    photo2_thumb.short_description = "Foto 2"
    photo3_thumb.short_description = "Foto 3"
