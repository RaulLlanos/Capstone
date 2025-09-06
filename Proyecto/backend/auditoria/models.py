# auditoria/models.py
from django.db import models
from asignaciones.models import DireccionAsignada

class AuditoriaVisita(models.Model):
    asignacion = models.ForeignKey(
        DireccionAsignada, on_delete=models.PROTECT, related_name='auditorias'
    )
    nombre_auditor = models.CharField(max_length=100)

    # snapshot
    marca = models.CharField(max_length=10)
    tecnologia = models.CharField(max_length=10)
    rut_cliente = models.CharField(max_length=20)
    id_vivienda = models.CharField(max_length=50)
    direccion_cliente = models.CharField(max_length=255)

    # Q5
    estado_cliente = models.CharField(max_length=20)

    # ⬇️ NUEVO: fotos (se guardan en MEDIA_ROOT/auditorias/YYYY/MM/DD/)
    foto_1 = models.ImageField(upload_to='auditorias/%Y/%m/%d/', null=True, blank=True)
    foto_2 = models.ImageField(upload_to='auditorias/%Y/%m/%d/', null=True, blank=True)
    foto_3 = models.ImageField(upload_to='auditorias/%Y/%m/%d/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Auditoría de Instalación'
        verbose_name_plural = 'Auditorías de Instalación'
        indexes = [
            models.Index(fields=['marca', 'tecnologia', 'estado_cliente']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Auditoría #{self.id} - {self.direccion_cliente}"


class Issue(models.Model):
    auditoria = models.ForeignKey(
        AuditoriaVisita, on_delete=models.CASCADE, related_name='issues'
    )
    servicio = models.CharField(max_length=10, blank=True)
    detalle = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Issue #{self.id} - {self.servicio}"
