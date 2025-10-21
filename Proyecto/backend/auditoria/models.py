# auditoria/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from asignaciones.models import DireccionAsignada


class Tri(models.IntegerChoices):
    SI = 1, "Sí"
    NO = 2, "No"
    NA = 3, "No Aplica"


class EstadoCliente(models.TextChoices):
    AUTORIZA      = "AUTORIZA", "Autoriza a ingresar"
    SIN_MORADORES = "SIN_MORADORES", "Sin Moradores"
    RECHAZA       = "RECHAZA", "Rechaza"
    CONTINGENCIA  = "CONTINGENCIA", "Contingencia externa"
    MASIVO        = "MASIVO", "Incidencia Masivo ClaroVTR"
    REAGENDA      = "REAGENDA", "Reagendó"


# Q8: servicios con problema
SERVICIO_CHOICES = (
    ("internet", "Internet"),
    ("tv", "TV"),
    ("fono", "Fono"),
    ("otro", "Otro"),
)

# Q9: categorías problema Internet
INTERNET_ISSUE_CHOICES = (
    ("lento", "Navegaba muy lento"),
    ("wifi_alcance", "Señal del Wifi con bajo alcance"),
    ("cortes", "Cortes/Días sin servicio"),
    ("intermitencia", "Intermitencia de la Señal de Internet"),
    ("otro", "Otro"),
)

# Q10: categorías problema TV
TV_ISSUE_CHOICES = (
    ("sin_senal", "Me quedaba sin señal de TV"),
    ("pixelado", "Se pixelaba la imagen de TV"),
    ("intermitencia", "Intermitencia de la Señal"),
    ("desfase", "Presenta desfase con la señal en vivo"),
    ("streaming", "Problemas con Plataforma de Streaming"),
    ("zapping", "Problemas para hacer Zapping (lentitud)"),
    ("equipos", "Problemas con Equipos (Dbox, Control, IPTV)"),
    ("otro", "Otro"),
)

# Q29/Q30/Q31/Q32
RESOLUTION_CHOICES = (
    ("terreno", "Se solucionó en terreno"),
    ("orden", "Se realizó una gestión con Orden"),
)
ORDER_TYPE_CHOICES = (
    ("tecnica", "Técnica"),
    ("comercial", "Comercial"),
)
INFO_TYPE_CHOICES = (
    ("mala_practica", "Mala Práctica"),
    ("problema_general", "Problema General"),
)


def _upload_auditoria(instance, filename):
    # Incluye el ID en la ruta (si no existe todavía, usa 'tmp')
    obj_id = instance.id or "tmp"
    return f"auditorias/{obj_id}/{filename}"


class AuditoriaVisita(models.Model):
    # Identificación
    asignacion = models.ForeignKey(DireccionAsignada, on_delete=models.CASCADE, related_name="auditorias")
    tecnico = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    # Q5 Estado del Cliente
    customer_status = models.CharField(
        max_length=20,
        choices=EstadoCliente.choices,
        blank=True,
        db_column="estado_cliente",
    )

    # Reagendamiento observado en auditoría
    reschedule_date = models.DateField(null=True, blank=True, db_column="reagendado_fecha")
    reschedule_slot = models.CharField(
        max_length=10, blank=True,
        help_text="Usar 10-13 o 14-18",
        db_column="reagendado_bloque",
    )

    # Q72 ONT/Modem correctamente instalado
    ont_modem_ok = models.PositiveSmallIntegerField(
        choices=Tri.choices,
        default=Tri.NA,
        db_column="q72_ont_ok",
    )

    # Q8 Servicio(s) con problema (checkboxes)
    service_issues = models.JSONField(default=list, blank=True, db_column="q8_servicios")

    # Q9 (si incluye Internet)
    internet_issue_category = models.CharField(
        max_length=32, choices=INTERNET_ISSUE_CHOICES, blank=True, db_column="q9_internet_categoria"
    )
    internet_issue_other = models.CharField(max_length=200, blank=True, db_column="q9_internet_otro")

    # Q10 (si incluye TV)
    tv_issue_category = models.CharField(
        max_length=32, choices=TV_ISSUE_CHOICES, blank=True, db_column="q10_tv_categoria"
    )
    tv_issue_other = models.CharField(max_length=200, blank=True, db_column="q10_tv_otro")

    # Q11 (si incluye “Otro” en servicios)
    other_issue_description = models.TextField(blank=True, db_column="q11_otro_descripcion")

    # Evidencias Q13–Q15
    photo1 = models.ImageField(upload_to=_upload_auditoria, blank=True, null=True, db_column="foto1")
    photo2 = models.ImageField(upload_to=_upload_auditoria, blank=True, null=True, db_column="foto2")
    photo3 = models.ImageField(upload_to=_upload_auditoria, blank=True, null=True, db_column="foto3")

    # Q73 (solo si tecnología = HFC)
    hfc_problem_description = models.TextField(blank=True, db_column="q73_desc_hfc")

    # Bloque AGENDAMIENTO (Q16) + comentarios (Q71)
    schedule_informed_datetime = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="agend_inf_fecha_hora"
    )
    schedule_informed_adult_required = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="agend_aviso_adulto"
    )
    schedule_informed_services = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="agend_comunicacion_servicios"
    )
    schedule_comments = models.TextField(blank=True, db_column="q71_agend_comentarios")

    # Llegada del técnico (Q17) + comentarios (Q18)
    arrival_within_slot = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="llego_en_horario"
    )
    identification_shown = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="se_identifico"
    )
    explained_before_start = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="explico_antes"
    )
    arrival_comments = models.TextField(blank=True, db_column="q18_llegada_comentarios")

    # Proceso de instalación (Q19) + comentarios (Q20)
    asked_equipment_location = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="consulto_ubicacion"
    )
    tidy_and_safe_install = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="ordenado_seguro"
    )
    tidy_cabling = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="cableado_prolijo"
    )
    verified_signal_levels = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="verifico_niveles"
    )
    install_process_comments = models.TextField(blank=True, db_column="q20_proceso_comentarios")

    # Configuración y pruebas (Q21) + comentarios (Q22)
    configured_router = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="config_router"
    )
    tested_device = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="probo_dispositivo"
    )
    tv_functioning = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="tv_ok"
    )
    left_instructions = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="dejo_instrucciones"
    )
    config_comments = models.TextField(blank=True, db_column="q22_config_comentarios")

    # Cierre (Q23) + comentarios (Q24)
    reviewed_with_client = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="revision_con_cliente"
    )
    got_consent_signature = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="pidio_conformidad"
    )
    left_contact_info = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="dejo_contacto"
    )
    closure_comments = models.TextField(blank=True, db_column="q24_cierre_comentarios")

    # Percepción y NPS
    perception_notes = models.TextField(blank=True, db_column="q25_percepcion")
    nps_process = models.PositiveSmallIntegerField(null=True, blank=True, db_column="nps_proceso")          # Q26 (0–10)
    nps_technician = models.PositiveSmallIntegerField(null=True, blank=True, db_column="nps_tecnico")       # Q27 (0–10)
    nps_brand = models.PositiveSmallIntegerField(null=True, blank=True, db_column="nps_claro_vtr")          # Q28 (0–10)

    # Solución y gestión (Q29–Q32)
    resolution = models.CharField(max_length=16, choices=RESOLUTION_CHOICES, blank=True, db_column="solucion_gestion")
    order_type = models.CharField(max_length=16, choices=ORDER_TYPE_CHOICES, blank=True, db_column="orden_tipo")
    info_type = models.CharField(max_length=20, choices=INFO_TYPE_CHOICES, blank=True, db_column="info_tipo")
    malpractice_company_detail = models.CharField(max_length=200, blank=True, db_column="detalle_mala_practica_empresa")
    malpractice_installer_detail = models.CharField(max_length=200, blank=True, db_column="detalle_mala_practica_instalador")

    # Finalizar (Q12)
    final_problem_description = models.TextField(blank=True, db_column="q12_descripcion_problema")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Auditoría #{self.id or 'nuevo'} - {self.asignacion.direccion} ({self.asignacion.comuna})"

    # Validaciones condicionales
    def clean(self):
        selected = set(self.service_issues or [])

        # Si hay Internet => requiere categoría
        if "internet" in selected and not self.internet_issue_category:
            raise ValidationError("Si marcaste 'Internet' debes elegir la categoría del problema (Internet).")
        if self.internet_issue_category == "otro" and not self.internet_issue_other:
            raise ValidationError("Describe el 'Otro' de Internet.")

        # Si hay TV => requiere categoría
        if "tv" in selected and not self.tv_issue_category:
            raise ValidationError("Si marcaste 'TV' debes elegir la categoría del problema (TV).")
        if self.tv_issue_category == "otro" and not self.tv_issue_other:
            raise ValidationError("Describe el 'Otro' de TV.")

        # Si hay 'otro' en servicios => exige detalle
        if "otro" in selected and not (self.other_issue_description or "").strip():
            raise ValidationError("Describe el 'Otro' (servicios).")

        # Gestión con orden => exige tipo
        if self.resolution == "orden" and not self.order_type:
            raise ValidationError("Selecciona el tipo de orden técnica.")

        # Mala práctica => exige detalle
        if self.info_type == "mala_practica":
            if not (self.malpractice_company_detail or self.malpractice_installer_detail):
                raise ValidationError("Agrega detalle de mala práctica (empresa o instalador).")

        # NPS 0–10
        for nps_value in (self.nps_process, self.nps_technician, self.nps_brand):
            if nps_value is not None and (nps_value < 0 or nps_value > 10):
                raise ValidationError("Las puntuaciones NPS deben estar entre 0 y 10.")
