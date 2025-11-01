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


# Servicios con problema (equiv. Q8)
SERVICE_CHOICES = (
    ("internet", "Internet"),
    ("tv", "TV"),
    ("fono", "Fono"),
    ("otro", "Otro"),
)

# Categorías problema Internet (equiv. Q9)
INTERNET_ISSUE_CHOICES = (
    ("lento", "Navegaba muy lento"),
    ("wifi_alcance", "Señal del Wifi con bajo alcance"),
    ("cortes", "Cortes/Días sin servicio"),
    ("intermitencia", "Intermitencia de la Señal de Internet"),
    ("otro", "Otro"),
)

# Categorías problema TV (equiv. Q10)
TV_ISSUE_CHOICES = (
    ("sin_senal", "Me quedaba sin señal de TV"),
    ("pixelado", "Se pixelaba la imagen de TV"),
    ("intermitencia", "Intermitencia de la Señal"),
    ("desfase", "Presenta desfase con la señal en vivo"),
    ("streaming", "Problemas con Plataforma de Streaming"),
    ("zapping", "Problemas con zapping (lentitud)"),
    ("equipos", "Problemas con Equipos (Dbox, Control, IPTV)"),
    ("otro", "Otro"),
)

# Resolución / gestión (equiv. Q29–Q32)
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
    # Ej: auditorias/123/foto.jpg (si aún no existe id, usa 'tmp')
    return f"auditorias/{getattr(instance, 'id', None) or 'tmp'}/{filename}"


class AuditoriaVisita(models.Model):
    # Identificación
    asignacion = models.ForeignKey(
        DireccionAsignada,
        on_delete=models.CASCADE,
        related_name="auditorias",
    )
    tecnico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Estado del cliente (Q5)
    customer_status = models.CharField(
        max_length=20,
        choices=EstadoCliente.choices,
        blank=True,
    )

    # Reagendamiento observado en auditoría (Q6–Q7)
    reschedule_date = models.DateField(null=True, blank=True, db_column="reagendado_fecha")
    reschedule_slot = models.CharField(
        max_length=10,
        blank=True,
        help_text="Usar 10-13 o 14-18",
        db_column="reagendado_bloque",
    )

    # ONT/Modem correctamente instalado (Q72)
    ont_modem_ok = models.PositiveSmallIntegerField(choices=Tri.choices, default=Tri.NA)

    # Servicio(s) con problema (checkboxes) (Q8)
    service_issues = models.JSONField(default=list, blank=True, db_column="servicios")

    # Internet (Q9)  >>> columnas renombradas en BD (sin db_column)
    internet_categoria = models.CharField(max_length=32, choices=INTERNET_ISSUE_CHOICES, blank=True)
    internet_otro      = models.CharField(max_length=200, blank=True)

    # TV (Q10)  >>> columnas renombradas en BD (sin db_column)
    tv_categoria = models.CharField(max_length=32, choices=TV_ISSUE_CHOICES, blank=True)
    tv_otro      = models.CharField(max_length=200, blank=True)

    # Otro (Q11)  >>> columna renombrada en BD (sin db_column)
    otro_descripcion = models.TextField(blank=True)

    # Evidencias (Q13–Q15) – fotos reales
    photo1 = models.ImageField(upload_to=_upload_auditoria, blank=True, null=True, db_column="foto1")
    photo2 = models.ImageField(upload_to=_upload_auditoria, blank=True, null=True, db_column="foto2")
    photo3 = models.ImageField(upload_to=_upload_auditoria, blank=True, null=True, db_column="foto3")

    # Solo HFC (Q73)  >>> columna renombrada en BD (sin db_column)
    desc_hfc = models.TextField(blank=True)

    # AGENDAMIENTO (Q16) + comentarios (Q71)
    schedule_informed_datetime = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="agend_inf_fecha_hora"
    )
    schedule_informed_adult_required = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="agend_aviso_adulto"
    )
    schedule_informed_services = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="agend_comunicacion_servicios"
    )
    # >>> columna renombrada en BD (sin db_column)
    agend_comentarios = models.TextField(blank=True)

    # Llegada del técnico (Q17/Q18)
    arrival_within_slot = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="llego_en_horario"
    )
    identification_shown = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="se_identifico"
    )
    explained_before_start = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="explico_antes"
    )
    # >>> columna renombrada en BD (sin db_column)
    llegada_comentarios = models.TextField(blank=True)

    # Proceso instalación (Q19/Q20)
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
    # >>> columna renombrada en BD (sin db_column)
    proceso_comentarios = models.TextField(blank=True)

    # Configuración y pruebas (Q21/Q22)
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
    # >>> columna renombrada en BD (sin db_column)
    config_comentarios = models.TextField(blank=True)

    # Cierre visita técnica (Q23/Q24)
    reviewed_with_client = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="revision_con_cliente"
    )
    got_consent_signature = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="pidio_conformidad"
    )
    left_contact_info = models.PositiveSmallIntegerField(
        choices=Tri.choices, default=Tri.NA, db_column="dejo_contacto"
    )
    # >>> columna renombrada en BD (sin db_column)
    cierre_comentarios = models.TextField(blank=True)

    # Percepción / NPS (Q25–Q28)
    # >>> columna renombrada en BD (sin db_column)
    percepcion = models.TextField(blank=True)
    nps_proceso = models.PositiveSmallIntegerField(null=True, blank=True, db_column="nps_proceso")
    nps_tecnico = models.PositiveSmallIntegerField(null=True, blank=True, db_column="nps_tecnico")
    nps_claro_vtr = models.PositiveSmallIntegerField(null=True, blank=True, db_column="nps_claro_vtr")

    # Solución / Gestión / Info (Q29–Q32)
    solucion_gestion = models.CharField(max_length=16, choices=RESOLUTION_CHOICES, blank=True, db_column="solucion_gestion")
    orden_tipo = models.CharField(max_length=16, choices=ORDER_TYPE_CHOICES, blank=True, db_column="orden_tipo")
    info_tipo = models.CharField(max_length=20, choices=INFO_TYPE_CHOICES, blank=True, db_column="info_tipo")
    detalle_mala_practica_empresa = models.CharField(max_length=200, blank=True, db_column="detalle_mala_practica_empresa")
    detalle_mala_practica_instalador = models.CharField(max_length=200, blank=True, db_column="detalle_mala_practica_instalador")

    # Finalizar (Q12)  >>> columna renombrada en BD (sin db_column)
    descripcion_problema = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Auditoría de visita"
        verbose_name_plural = "Auditorías de visitas"

    def __str__(self):
        a = getattr(self, "asignacion", None)
        return f"Auditoría #{self.id or 'nuevo'} - {a.direccion if a else '-'} ({a.comuna if a else '-'})"

    # Validaciones condicionales
    def clean(self):
        selected = set(self.service_issues or [])

        # Internet => requiere categoría
        if "internet" in selected and not self.internet_categoria:
            raise ValidationError("Si marcaste 'Internet', elige la categoría del problema.")
        if self.internet_categoria == "otro" and not self.internet_otro:
            raise ValidationError("Describe el 'Otro' de Internet.")

        # TV => requiere categoría
        if "tv" in selected and not self.tv_categoria:
            raise ValidationError("Si marcaste 'TV', elige la categoría del problema.")
        if self.tv_categoria == "otro" and not self.tv_otro:
            raise ValidationError("Describe el 'Otro' de TV.")

        # 'Otro' en servicios => exige detalle
        if "otro" in selected and not (self.otro_descripcion or "").strip():
            raise ValidationError("Describe el 'Otro' (servicios).")

        # Gestión con orden => exige tipo
        if self.solucion_gestion == "orden" and not self.orden_tipo:
            raise ValidationError("Selecciona el tipo de orden técnica.")

        # Mala práctica => exige detalle
        if self.info_tipo == "mala_practica":
            if not (self.detalle_mala_practica_empresa or self.detalle_mala_practica_instalador):
                raise ValidationError("Agrega detalle de mala práctica (empresa o instalador).")

        # NPS 0–10
        for nps in (self.nps_proceso, self.nps_tecnico, self.nps_claro_vtr):
            if nps is not None and (nps < 0 or nps > 10):
                raise ValidationError("Las puntuaciones NPS deben estar entre 0 y 10.")
