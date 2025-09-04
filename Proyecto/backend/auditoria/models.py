from django.db import models

from usuarios.models import Usuario

# Create your models here.

class AuditoriaInstalacion(models.Model):
    ESTADOS_CLIENTE = (
        ('autoriza', 'Autoriza a ingresar'),
        ('sin_moradores', 'Sin Moradores'),
        ('rechaza', 'Rechaza'),
        ('contingencia', 'Contingencia externa'),
        ('masivo', 'Incidencia Masivo ClaroVTR'),
        ('reagendo', 'Reagendó'),
    )
    
    TECNOLOGIAS = (
        ('hfc', 'HFC'),
        ('nftt', 'NFTT'), 
        ('ftth', 'FTTH'),
    )
    
    MARCAS = (
        ('claro', 'CLARO'),
        ('vtr', 'VTR'),
    )
    
    BLOQUES_HORARIOS = (
        ('10-13', '10:00 a 13:00'),
        ('14-18', '14:00 a 18:00'),
    )
    
    # Información básica
    tecnico = models.ForeignKey(Usuario, on_delete=models.CASCADE, limit_choices_to={'rol': 'tecnico'})
    fecha_auditoria = models.DateTimeField(auto_now_add=True)
    nombre_auditor = models.CharField(max_length=100)
    
    # Identificadores del cliente
    rut_cliente = models.CharField(max_length=12)
    id_vivienda = models.CharField(max_length=50)
    direccion_cliente = models.TextField()
    
    # Datos técnicos
    marca = models.CharField(max_length=10, choices=MARCAS)
    tecnologia = models.CharField(max_length=10, choices=TECNOLOGIAS)
    estado_cliente = models.CharField(max_length=20, choices=ESTADOS_CLIENTE)
    
    # Campos condicionales
    fecha_reagendamiento = models.DateField(null=True, blank=True)
    bloque_horario = models.CharField(max_length=20, choices=BLOQUES_HORARIOS, null=True, blank=True)
    
    # Problemas y verificaciones
    ont_instalada_correctamente = models.BooleanField(null=True, blank=True)
    servicios_problema = models.JSONField(default=list, blank=True)  # Para múltiples selecciones
    
    # Evaluaciones (pueden ser JSON o campos separados)
    evaluacion_agendamiento = models.JSONField(default=dict, blank=True)
    evaluacion_llegada = models.JSONField(default=dict, blank=True)
    evaluacion_instalacion = models.JSONField(default=dict, blank=True)
    evaluacion_configuracion = models.JSONField(default=dict, blank=True)
    evaluacion_cierre = models.JSONField(default=dict, blank=True)
    
    # Percepción del cliente
    puntuacion_proceso = models.IntegerField(null=True, blank=True)
    puntuacion_tecnico = models.IntegerField(null=True, blank=True)
    puntuacion_recomendacion = models.IntegerField(null=True, blank=True)
    
    # Solución y gestión
    solucion_gestion = models.CharField(max_length=50, blank=True)
    tipo_orden_gestionada = models.CharField(max_length=50, blank=True)
    tipo_problema = models.CharField(max_length=50, blank=True)
    detalle_mala_practica = models.TextField(blank=True)
    
    # Comentarios y descripciones
    comentarios_agendamiento = models.TextField(blank=True)
    comentarios_llegada = models.TextField(blank=True)
    comentarios_instalacion = models.TextField(blank=True)
    comentarios_configuracion = models.TextField(blank=True)
    comentarios_cierre = models.TextField(blank=True)
    descripcion_problema = models.TextField(blank=True)
    
    # Fotos (opcional - si quieres guardar rutas de archivos)
    foto_1_ruta = models.CharField(max_length=255, blank=True)
    foto_2_ruta = models.CharField(max_length=255, blank=True)
    foto_3_ruta = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Auditoría de Instalación'
        verbose_name_plural = 'Auditorías de Instalación'

    def __str__(self):
        return f"Auditoría {self.id} - {self.direccion_cliente}"