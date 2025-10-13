from django.db import models
from django.conf import settings

class AuditoriaVisita(models.Model):
    ESTADO_CLIENTE = (
        ("autoriza", "Autoriza a ingresar"),
        ("sin_moradores", "Sin Moradores"),
        ("rechaza", "Rechaza"),
        ("contingencia", "Contingencia externa"),
        ("masivo", "Incidencia Masivo ClaroVTR"),
        ("reagendo", "Reagendó"),
    )
    BLOQUES = (("10-13", "10:00-13:00"), ("14-18", "14:00-18:00"))

    asignacion = models.ForeignKey("asignaciones.DireccionAsignada", on_delete=models.PROTECT, related_name="auditorias")
    tecnico    = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    # Q5
    estado_cliente = models.CharField(max_length=20, choices=ESTADO_CLIENTE)

    # Si reagendó (Q6, Q7)
    reagendado_fecha = models.DateField(null=True, blank=True)
    reagendado_bloque = models.CharField(max_length=10, choices=BLOQUES, null=True, blank=True)

    # Q72
    ont_modem_ok = models.BooleanField(null=True, blank=True)

    # Q8..Q11/Q73
    servicios = models.JSONField(default=list, blank=True)     # p.ej. ["internet","tv"]
    categorias = models.JSONField(default=dict, blank=True)    # p.ej. {"internet":["cortes","intermitencia"], "tv":["pixelado"]}
    descripcion_problema = models.TextField(blank=True, default="")

    # Fotos simples (rutas/URLs o nombres de archivo)
    fotos = models.JSONField(default=list, blank=True)

    # Bloques de cuestionario (Q16..Q32 etc.)
    bloque_agendamiento = models.JSONField(default=dict, blank=True)
    bloque_llegada      = models.JSONField(default=dict, blank=True)
    bloque_proceso      = models.JSONField(default=dict, blank=True)
    bloque_config       = models.JSONField(default=dict, blank=True)
    bloque_cierre       = models.JSONField(default=dict, blank=True)
    percepcion          = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"], name="auditoria_a_created_bb8ea3_idx"),
            models.Index(fields=["estado_cliente"], name="auditoria_estado_idx"),
            models.Index(fields=["asignacion", "-created_at"], name="auditoria_asig_created_idx"),
        ]

    def __str__(self):
        return f"AuditoriaVisita #{self.id} ({self.estado_cliente})"
