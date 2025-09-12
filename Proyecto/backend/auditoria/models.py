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

    asignacion = models.ForeignKey(
        Asignacion, on_delete=models.PROTECT, related_name="auditorias", verbose_name="Dirección"
    )

    # Snapshot (al crear)
    marca             = models.CharField("Marca", max_length=10)
    tecnologia        = models.CharField("Tecnología", max_length=10)
    rut_cliente       = models.CharField("RUT cliente", max_length=20, blank=True, null=True)
    id_vivienda       = models.CharField("ID vivienda", max_length=50, blank=True, null=True)
    direccion_cliente = models.CharField("Dirección del cliente", max_length=255)

    # Q5
    estado_cliente = models.CharField("Estado del cliente", max_length=20, choices=EstadoCliente.choices)

    # Q72
    ont_modem_ok = models.BooleanField("ONT/Modem bien instalado", blank=True, null=True)

    # Bloques flexibles (JSON para Si/No/No Aplica + comentarios)
    bloque_agendamiento = models.JSONField("Bloque: Agendamiento", blank=True, null=True)
    bloque_llegada      = models.JSONField("Bloque: Llegada del técnico", blank=True, null=True)
    bloque_proceso      = models.JSONField("Bloque: Proceso de instalación", blank=True, null=True)
    bloque_config       = models.JSONField("Bloque: Configuración y pruebas", blank=True, null=True)
    bloque_cierre       = models.JSONField("Bloque: Cierre de visita técnica", blank=True, null=True)
    percepcion          = models.JSONField("Percepción del cliente", blank=True, null=True)

    descripcion_problema = models.TextField("Descripción del problema", blank=True, null=True)

    created_at = models.DateTimeField("Creado", auto_now_add=True)

    class Meta:
        db_table = "auditorias"
        verbose_name = "Auditoría"
        verbose_name_plural = "Auditorías"
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

    auditoria = models.ForeignKey(Auditoria, on_delete=models.CASCADE, related_name="servicios", verbose_name="Auditoría")
    servicio  = models.CharField("Servicio", max_length=10, choices=Servicio.choices)

    class Meta:
        db_table = "auditoria_servicios"
        verbose_name = "Servicio en auditoría"
        verbose_name_plural = "Servicios en auditoría"

    def __str__(self):
        return f"Servicio {self.servicio} (Auditoría {self.auditoria_id})"

class AuditoriaCategoria(models.Model):
    auditoria_servicio = models.ForeignKey(
        AuditoriaServicio, on_delete=models.CASCADE, related_name="categorias",
        verbose_name="Servicio en auditoría"
    )
    categoria = models.CharField("Categoría", max_length=100)  # Ej.: "Navegaba muy lento"
    extra     = models.TextField("Detalle adicional", blank=True, null=True)  # Para "Otro. ¿Cuál?"

    class Meta:
        db_table = "auditoria_categorias"
        verbose_name = "Categoría de servicio"
        verbose_name_plural = "Categorías de servicio"

    def __str__(self):
        return f"Cat '{self.categoria}' (Serv {self.auditoria_servicio_id})"

class EvidenciaServicio(models.Model):
    class Tipo(models.TextChoices):
        FOTO        = "foto",        "Foto"
        FIRMA       = "firma",       "Firma"
        COMPROBANTE = "comprobante", "Comprobante"
        OTRO        = "otro",        "Otro"

    auditoria  = models.ForeignKey(Auditoria, on_delete=models.CASCADE, related_name="evidencias",
                                   blank=True, null=True, verbose_name="Auditoría")
    asignacion = models.ForeignKey(Asignacion, on_delete=models.CASCADE, related_name="evidencias",
                                   verbose_name="Dirección")
    tipo       = models.CharField("Tipo", max_length=20, choices=Tipo.choices, default=Tipo.FOTO)
    archivo    = models.ImageField("Archivo", upload_to="auditorias/%Y/%m/%d/")
    descripcion = models.TextField("Descripción", blank=True, null=True)
    usuario     = models.ForeignKey(Usuario, on_delete=models.RESTRICT, verbose_name="Usuario")
    created_at  = models.DateTimeField("Creado", auto_now_add=True)

    class Meta:
        db_table = "evidencias_servicio"
        verbose_name = "Evidencia"
        verbose_name_plural = "Evidencias"

    def __str__(self):
        return f"Evidencia {self.tipo} #{self.id}"
