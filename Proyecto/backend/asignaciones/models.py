from django.db import models
from django.db.models import Q
from usuarios.models import Usuario

class Marca(models.TextChoices):
    CLARO = "CLARO", "CLARO"
    VTR   = "VTR",   "VTR"

class Tecnologia(models.TextChoices):
    HFC  = "HFC",  "HFC"
    NFTT = "NFTT", "NFTT"
    FTTH = "FTTH", "FTTH"

class TipoEncuesta(models.TextChoices):
    POST_VISITA = "post_visita", "post visita"
    INSTALACION = "instalacion", "instalación"
    OPERACIONES = "operaciones", "operaciones"

class EstadoAsignacion(models.TextChoices):
    PENDIENTE  = "PENDIENTE",  "Pendiente"
    ASIGNADA   = "ASIGNADA",   "Asignada"
    VISITADA   = "VISITADA",   "Visitada"
    CANCELADA  = "CANCELADA",  "Cancelada"
    REAGENDADA = "REAGENDADA", "Reagendada"

class BloqueHorario(models.TextChoices):
    DIEZ_TRECE        = "10-13", "10:00 a 13:00"
    CATORCE_DIECIOCHO = "14-18", "14:00 a 18:00"

class ZonaSantiago(models.TextChoices):
    NORTE  = "NORTE",  "Norte"
    CENTRO = "CENTRO", "Centro"
    SUR    = "SUR",    "Sur"

class DireccionAsignada(models.Model):
    fecha       = models.DateField(null=True, blank=True)
    tecnologia  = models.CharField(max_length=10, choices=Tecnologia.choices)
    marca       = models.CharField(max_length=10, choices=Marca.choices)
    rut_cliente = models.CharField(max_length=20)
    id_vivienda = models.CharField(max_length=50)
    direccion   = models.CharField(max_length=255)
    comuna      = models.CharField(max_length=80, blank=True)  # opcional (útil para filtros)
    zona        = models.CharField(max_length=10, choices=ZonaSantiago.choices, blank=True)  # NORTE/CENTRO/SUR

    encuesta     = models.CharField(max_length=20, choices=TipoEncuesta.choices)
    id_qualtrics = models.CharField(max_length=64, blank=True)

    asignado_a = models.ForeignKey(
        Usuario, null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={"rol": "tecnico"}
    )

    estado = models.CharField(
        max_length=10, choices=EstadoAsignacion.choices, default=EstadoAsignacion.PENDIENTE
    )

    # reagendamiento efectivo (último)
    reagendado_fecha  = models.DateField(null=True, blank=True)
    reagendado_bloque = models.CharField(max_length=5, choices=BloqueHorario.choices, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "asignaciones"
        indexes = [
            models.Index(fields=["rut_cliente", "id_vivienda"]),
            models.Index(fields=["marca", "tecnologia"]),
            models.Index(fields=["encuesta"]),
            models.Index(fields=["comuna"]),
            models.Index(fields=["zona"]),
        ]
        # Evita tener *más de una* asignación activa (con técnico asignado) para el mismo cliente/vivienda
        constraints = [
            models.UniqueConstraint(
                fields=["rut_cliente", "id_vivienda"],
                condition=Q(asignado_a__isnull=False) & Q(estado__in=["PENDIENTE", "ASIGNADA", "REAGENDADA"]),
                name="uniq_activa_por_cliente_vivienda"
            )
        ]

    def __str__(self):
        who = self.asignado_a.email if self.asignado_a else "sin asignar"
        return f"{self.direccion} ({self.marca}/{self.tecnologia}) → {who}"

# ---- Trazabilidad ----
class Reagendamiento(models.Model):
    asignacion = models.ForeignKey(DireccionAsignada, on_delete=models.CASCADE, related_name="reagendamientos")
    fecha_anterior   = models.DateField(null=True, blank=True)
    bloque_anterior  = models.CharField(max_length=5, choices=BloqueHorario.choices, null=True, blank=True)
    fecha_nueva      = models.DateField()
    bloque_nuevo     = models.CharField(max_length=5, choices=BloqueHorario.choices)
    motivo           = models.TextField()
    usuario          = models.ForeignKey(Usuario, on_delete=models.RESTRICT)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reagendamientos"

    def __str__(self):
        return f"Reagendamiento #{self.id} → {self.asignacion_id}"

class HistorialAsignacion(models.Model):
    class Accion(models.TextChoices):
        CREADA            = "CREADA", "Creada"
        ASIGNADA_TECNICO  = "ASIGNADA_TECNICO", "Asignada a técnico"
        ESTADO_CLIENTE    = "ESTADO_CLIENTE",   "Estado del cliente"
        REAGENDADA        = "REAGENDADA",       "Reagendada"
        CERRADA           = "CERRADA",          "Cerrada"
        AUDITORIA_CREADA  = "AUDITORIA_CREADA", "Auditoría creada"

    asignacion = models.ForeignKey(DireccionAsignada, on_delete=models.CASCADE, related_name="historial")
    accion     = models.CharField(max_length=32, choices=Accion.choices)
    detalles   = models.TextField(blank=True)
    usuario    = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_asignaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"H{self.id} {self.accion} @A{self.asignacion_id}"

# ---- Alias para compatibilidad con otras apps ----
Asignacion = DireccionAsignada
