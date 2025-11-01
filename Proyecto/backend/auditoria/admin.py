# auditoria/admin.py
from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import (
    AuditoriaVisita,
    Tri,
    EstadoCliente,   # lo puedes usar si te sirve para choices en otros lados
)

# ✅ Fallback local de opciones para los checkboxes de "service_issues"
#    (no dependemos de constantes del models.py)
SERVICE_ISSUES_CHOICES = (
    ("internet", "Internet"),
    ("tv", "TV"),
    ("fono", "Fono"),
    ("otro", "Otro"),
)


class AuditoriaVisitaForm(forms.ModelForm):
    # checkboxes múltiples desde JSONField
    service_issues = forms.MultipleChoiceField(
        choices=SERVICE_ISSUES_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = AuditoriaVisita
        exclude = ()
        widgets = {
            # Radios para Tri
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

            # Selects por defecto para CharField con choices
            "customer_status": forms.Select,
            "internet_issue_category": forms.Select,
            "tv_issue_category": forms.Select,
            "resolution": forms.Select,
            "order_type": forms.Select,
            "info_type": forms.Select,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Inicializar checkboxes desde JSON list
        if self.instance and self.instance.pk and isinstance(self.instance.service_issues, list):
            self.fields["service_issues"].initial = self.instance.service_issues

        # Ayudas
        if "reschedule_slot" in self.fields:
            self.fields["reschedule_slot"].help_text = "Use 10-13 o 14-18"
        for nps in ("nps_process", "nps_technician", "nps_brand"):
            if nps in self.fields:
                self.fields[nps].help_text = "Rango 0 a 10"

    def clean(self):
        cleaned = super().clean()
        # Persistir checkboxes al JSONField
        servicios = cleaned.get("service_issues") or []
        self.instance.service_issues = list(servicios)
        return cleaned


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

    # 👇 Estos filtros requieren que 'resolution' e 'info_type' EXISTAN en el modelo
    #    (ya los tienes tras la migración 0007). Si aún no migras, comenta estas dos líneas.
    list_filter = (
        "customer_status",
        "ont_modem_ok",
        "solucion_gestion",   # antes: resolution
        "info_tipo",  # antes: info_type
        ("created_at", admin.DateFieldListFilter),
    )

    search_fields = ("asignacion__direccion", "asignacion__comuna", "tecnico__email")
    readonly_fields = ("created_at",)

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
        ("Servicio con problema", {
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
            "fields": ("created_at",)
        }),
    )

    # Helpers
    def asignacion_str(self, obj):
        a = obj.asignacion
        return f"{a.direccion} ({a.comuna})" if a else "-"
    asignacion_str.short_description = "Dirección"

    def services_str(self, obj):
        if not obj.service_issues:
            return "-"
        label_by_val = dict(SERVICE_ISSUES_CHOICES)
        return ", ".join(label_by_val.get(v, v) for v in obj.service_issues)
    services_str.short_description = "Servicios"

    # Thumbnails de fotos
    def _thumb(self, filefield):
        if not filefield:
            return "-"
        try:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', filefield.url)
        except Exception:
            return "-"

    def photo1_thumb(self, obj): return self._thumb(getattr(obj, "photo1", None))
    def photo2_thumb(self, obj): return self._thumb(getattr(obj, "photo2", None))
    def photo3_thumb(self, obj): return self._thumb(getattr(obj, "photo3", None))

    photo1_thumb.short_description = "Foto 1"
    photo2_thumb.short_description = "Foto 2"
    photo3_thumb.short_description = "Foto 3"
