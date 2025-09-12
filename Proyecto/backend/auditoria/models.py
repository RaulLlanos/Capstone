from django.db import models
from asignaciones.models import Asignacion  # alias de DireccionAsignada
from usuarios.models import Usuario

class Auditoria(models.Model):
    class EstadoCliente(models.TextChoices):
        AUTORIZA       = "autoriza",       "Autoriza a ingresar"
        SIN_MORADORES  = "sin_moradores",  "Sin Moradores"
        RECHAZA        = "rechaza",        "Rechaza"
        CONTINGENCIA   = "contingencia",   "Contingencia externa"
        MASIVO         = "masivo",         "Incidencia Masivo ClaroVTR"
        REAGENDO       = "reagendo",       "Reagendó"

    asignacion = models.ForeignKey(Asignacion, on_delete=models.PROTECT, related_name="auditorias")

    # Snapshot (al crear)
    marca             = models.CharField(max_length=10)
    tecnologia        = models.CharField(max_length=10)
    rut_cliente       = models.CharField(max_length=20, blank=True, null=True)
    id_vivienda       = models.CharField(max_length=50, blank=True, null=True)
    direccion_cliente = models.CharField(max_length=255)

    # Q5
    estado_cliente = models.CharField(max_length=20, choices=EstadoCliente.choices)

    # Q72
    ont_modem_ok = models.BooleanField(blank=True, null=True)

    # Bloques flexibles
    bloque_agendamiento = models.JSONField(blank=True, null=True)  # Q16/Q71
    bloque_llegada      = models.JSONField(blank=True, null=True)  # Q17/Q18
    bloque_proceso      = models.JSONField(blank=True, null=True)  # Q19/Q20
    bloque_config       = models.JSONField(blank=True, null=True)  # Q21/Q22
    bloque_cierre       = models.JSONField(blank=True, null=True)  # Q23/Q24
    percepcion          = models.JSONField(blank=True, null=True)  # Q25..Q32

    descripcion_problema = models.TextField(blank=True, null=True)  # Q12 (y Q73 si HFC en el front)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "auditorias"
        indexes = [
            models.Index(fields=["marca", "tecnologia", "estado_cliente"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Auditoría #{self.id} - {self.direccion_cliente}"

class AuditoriaServicio(models.Model):
    class Servicio(models.TextChoices):
        INTERNET = "internet", "Internet"
        TV       = "tv",       "TV"
        FONO     = "fono",     "Fono"
        OTRO     = "otro",     "Otro"

    auditoria = models.ForeignKey(Auditoria, on_delete=models.CASCADE, related_name="servicios")
    servicio  = models.CharField(max_length=10, choices=Servicio.choices)

    class Meta:
        db_table = "auditoria_servicios"

    def __str__(self):
        return f"Servicio {self.servicio} (Auditoría {self.auditoria_id})"

class AuditoriaCategoria(models.Model):
    auditoria_servicio = models.ForeignKey(AuditoriaServicio, on_delete=models.CASCADE, related_name="categorias")
    categoria = models.CharField(max_length=100)  # Ej.: "Navegaba muy lento"
    extra     = models.TextField(blank=True, null=True)  # Para "Otro. ¿Cuál?"

    class Meta:
        db_table = "auditoria_categorias"

    def __str__(self):
        return f"Cat '{self.categoria}' (Serv {self.auditoria_servicio_id})"

class EvidenciaServicio(models.Model):
    class Tipo(models.TextChoices):
        FOTO        = "foto",        "Foto"
        FIRMA       = "firma",       "Firma"
        COMPROBANTE = "comprobante", "Comprobante"
        OTRO        = "otro",        "Otro"

    auditoria  = models.ForeignKey(Auditoria, on_delete=models.CASCADE, related_name="evidencias", blank=True, null=True)
    asignacion = models.ForeignKey(Asignacion, on_delete=models.CASCADE, related_name="evidencias")
    tipo       = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.FOTO)
    archivo    = models.ImageField(upload_to="auditorias/%Y/%m/%d/")
    descripcion = models.TextField(blank=True, null=True)
    usuario     = models.ForeignKey(Usuario, on_delete=models.RESTRICT)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "evidencias_servicio"

    def __str__(self):
        return f"Evidencia {self.tipo} #{self.id}"
