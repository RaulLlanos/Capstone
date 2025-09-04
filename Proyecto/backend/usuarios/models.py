from django.db import models

from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un email')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractUser):
    ROLES = (
        ('tecnico', 'Técnico'),
        ('auditor', 'Auditor'), 
        ('admin', 'Administrador'),
    )
    
    # Campos personalizados
    rut_usuario = models.CharField(max_length=12, unique=True, null=True, blank=True, verbose_name='RUT')
    rol = models.CharField(max_length=10, choices=ROLES, default='tecnico', verbose_name='Rol')
    
    # SOBREESCRIBIR campos de AbstractUser para español
    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellido')  
    email = models.EmailField(unique=True, verbose_name='Email')
    
    # Configuración
    username = None  # Deshabilitar username
    USERNAME_FIELD = 'email'  # Usar email para login
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Campos requeridos
    objects = UsuarioManager()  # Usar el manager personalizado
    
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Tecnico(models.Model):
    id_tecnico = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, db_column='usuario_id', verbose_name='Usuario')
    zona = models.CharField(max_length=50, verbose_name='Zona')

    class Meta:
        db_table = 'tecnicos'
        verbose_name = 'Técnico'
        verbose_name_plural = 'Técnicos'

    def __str__(self):
        return f"Técnico {self.usuario.nombre_usuario} - Zona {self.zona}"


class Visita(models.Model):
    ESTADOS = (
        ('programada', 'Programada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('reagendada', 'Reagendada'),
        ('cancelada', 'Cancelada'),
    )
    
    TIPOS_SERVICIO = (
        ('instalacion', 'Instalación'),
        ('mantenimiento', 'Mantenimiento'),
        ('reparacion', 'Reparación'),
        ('otro', 'Otro'),
    )
    
    id_visita = models.AutoField(primary_key=True)
    tecnico = models.ForeignKey(Tecnico, on_delete=models.CASCADE, db_column='tecnico_id', verbose_name='Técnico')
    cliente_nombre = models.CharField(max_length=100, verbose_name='Nombre Cliente')
    cliente_apellido = models.CharField(max_length=100, verbose_name='Apellido Cliente')
    cliente_direccion = models.TextField(verbose_name='Dirección')
    cliente_comuna = models.CharField(max_length=50, verbose_name='Comuna')
    cliente_telefono = models.CharField(max_length=20, verbose_name='Teléfono Cliente')
    fecha_programada = models.DateField(verbose_name='Fecha Programada')
    hora_programada = models.TimeField(verbose_name='Hora Programada')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programada', verbose_name='Estado')
    tipo_servicio = models.CharField(max_length=20, choices=TIPOS_SERVICIO, verbose_name='Tipo de Servicio')
    descripcion_servicio = models.TextField(null=True, blank=True, verbose_name='Descripción del Servicio')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')

    class Meta:
        db_table = 'visitas'
        verbose_name = 'Visita'
        verbose_name_plural = 'Visitas'

    def __str__(self):
        return f"Visita {self.id_visita} - {self.cliente_nombre}"


class Reagendamiento(models.Model):
    id_reagendamiento = models.AutoField(primary_key=True)
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, db_column='visita_id', verbose_name='Visita')
    fecha_anterior = models.DateField(verbose_name='Fecha Anterior')
    hora_anterior = models.TimeField(verbose_name='Hora Anterior')
    fecha_nueva = models.DateField(verbose_name='Fecha Nueva')
    hora_nueva = models.TimeField(verbose_name='Hora Nueva')
    motivo = models.TextField(verbose_name='Motivo')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='usuario_id', verbose_name='Usuario')
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')

    class Meta:
        db_table = 'reagendamientos'
        verbose_name = 'Reagendamiento'
        verbose_name_plural = 'Reagendamientos'

    def __str__(self):
        return f"Reagendamiento {self.id_reagendamiento} - Visita {self.visita.id_visita}"


class HistorialVisita(models.Model):
    ACCIONES = (
        ('creada', 'Creada'),
        ('reagendada', 'Reagendada'),
        ('completada', 'Completada'),
        ('nota_agregada', 'Nota Agregada'),
        ('cancelada', 'Cancelada'),
        ('estado_cambiado', 'Estado Cambiado'),
    )
    
    id_historial = models.AutoField(primary_key=True)
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, db_column='visita_id', verbose_name='Visita')
    accion = models.CharField(max_length=20, choices=ACCIONES, verbose_name='Acción')
    detalles = models.TextField(null=True, blank=True, verbose_name='Detalles')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='usuario_id', verbose_name='Usuario')
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')

    class Meta:
        db_table = 'historial_visitas'
        verbose_name = 'Historial de Visita'
        verbose_name_plural = 'Historial de Visitas'

    def __str__(self):
        return f"Historial {self.id_historial} - {self.accion}"


class EvidenciaServicio(models.Model):
    TIPOS_EVIDENCIA = (
        ('foto', 'Foto'),
        ('firma', 'Firma'),
        ('comprobante', 'Comprobante'),
        ('otro', 'Otro'),
    )
    
    id_evidencia = models.AutoField(primary_key=True)
    visita = models.ForeignKey(Visita, on_delete=models.CASCADE, db_column='visita_id', verbose_name='Visita')
    tipo_evidencia = models.CharField(max_length=20, choices=TIPOS_EVIDENCIA, default='foto', verbose_name='Tipo de Evidencia')
    archivo_ruta = models.CharField(max_length=255, verbose_name='Ruta de Archivo')
    descripcion = models.TextField(null=True, blank=True, verbose_name='Descripción')
    fecha_hora = models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, db_column='usuario_id', verbose_name='Usuario')

    class Meta:
        db_table = 'evidencias_servicio'
        verbose_name = 'Evidencia de Servicio'
        verbose_name_plural = 'Evidencias de Servicio'

    def __str__(self):
        return f"Evidencia {self.id_evidencia} - {self.tipo_evidencia}"