from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# ===== Manager =====
class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Superusuario solo para /admin; la API se maneja con rol (administrador/tecnico)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

# ===== Usuario =====
class Usuario(AbstractUser):
    ROLES = (
        ("tecnico", "Técnico"),
        ("administrador", "Administrador"),
    )

    # Deshabilitamos username
    username = None

    # Login por email
    email = models.EmailField(unique=True, verbose_name="Email")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    # Nombres
    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name  = models.CharField(max_length=100, verbose_name="Apellido")

    # Rol
    rol = models.CharField(max_length=20, choices=ROLES, default="tecnico", verbose_name="Rol")

    # RUT opción B: número y dígito verificador
    rut_num = models.PositiveIntegerField(null=True, blank=True, verbose_name="RUT (número sin DV)")
    dv      = models.CharField(max_length=1, null=True, blank=True, verbose_name="Dígito verificador")

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        constraints = [
            models.UniqueConstraint(
                fields=["rut_num", "dv"],
                name="uniq_usuario_rutnum_dv",
                condition=models.Q(rut_num__isnull=False, dv__isnull=False),
            )
        ]

    objects = UsuarioManager()

    @property
    def rut(self) -> str:
        if self.rut_num is None or not self.dv:
            return ""
        return f"{self.rut_num}-{self.dv.upper()}"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
