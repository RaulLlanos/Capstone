# asignaciones/models.py
from django.db import models
from usuarios.models import Usuario  # <- ya lo tienes

class Marca(models.TextChoices):
    CLARO = 'CLARO', 'CLARO'
    VTR = 'VTR', 'VTR'

class Tecnologia(models.TextChoices):
    HFC = 'HFC', 'HFC'
    NFTT = 'NFTT', 'NFTT'
    FTTH = 'FTTH', 'FTTH'

class TipoEncuesta(models.TextChoices):
    POST_VISITA = 'post_visita', 'post visita'
    INSTALACION = 'instalacion', 'instalación'
    OPERACIONES = 'operaciones', 'operaciones'

# ⬇️ añade estos 2 (nuevo estado + bloques)
class EstadoAsignacion(models.TextChoices):
    PENDIENTE  = 'PENDIENTE',  'Pendiente'
    ASIGNADA   = 'ASIGNADA',   'Asignada'
    VISITADA   = 'VISITADA',   'Visitada'
    CANCELADA  = 'CANCELADA',  'Cancelada'
    REAGENDADA = 'REAGENDADA', 'Reagendada'

class BloqueHorario(models.TextChoices):
    DIEZ_TRECE        = '10-13', '10:00 a 13:00'
    CATORCE_DIECIOCHO = '14-18', '14:00 a 18:00'

class DireccionAsignada(models.Model):
    fecha = models.DateField()
    tecnologia = models.CharField(
        max_length=10, choices=Tecnologia.choices, help_text="Tecnología del servicio (FTTH/HFC/NFTT)."
    )
    marca = models.CharField(max_length=10, choices=Marca.choices)
    rut_cliente = models.CharField(max_length=20)
    id_vivienda = models.CharField(max_length=50)
    direccion = models.CharField(max_length=255)
    encuesta = models.CharField(max_length=20, choices=TipoEncuesta.choices)
    id_qualtrics = models.CharField(max_length=64, blank=True)

    asignado_a = models.ForeignKey(
        Usuario, null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'rol': 'tecnico'}
    )

    # mantiene tu campo de estado pero ahora con las nuevas opciones
    estado = models.CharField(
        max_length=10,
        choices=EstadoAsignacion.choices,
        default=EstadoAsignacion.PENDIENTE
    )

    # ⬇️ CAMPOS NUEVOS de reagendamiento
    reagendado_fecha  = models.DateField(null=True, blank=True)
    reagendado_bloque = models.CharField(
        max_length=5,
        choices=BloqueHorario.choices,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['rut_cliente', 'id_vivienda']),
            models.Index(fields=['marca', 'tecnologia']),
            models.Index(fields=['encuesta']),
        ]

    def __str__(self):
        who = self.asignado_a.email if self.asignado_a else 'sin asignar'
        return f"{self.direccion} ({self.marca}/{self.tecnologia}) → {who}"
