from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = "Crea o actualiza un usuario admin (y opcionalmente un técnico) a partir de variables BOOTSTRAP_*"

    def _upsert_user(self, *, email, password, first_name, last_name, rol, is_staff, is_superuser):
        if not email or not password:
            self.stdout.write(self.style.WARNING(f"Saltando {rol}: faltan email/password"))
            return None, False

        # Busca case-insensitive
        u = User.objects.filter(email__iexact=email).first()
        created = False
        if u is None:
            u = User(email=email)
            created = True

        # Atributos
        u.first_name = first_name or ""
        u.last_name  = last_name or ""
        u.is_active  = True
        u.is_staff   = bool(is_staff)
        u.is_superuser = bool(is_superuser)
        # Si tu modelo tiene el campo 'rol'
        if hasattr(u, "rol"):
            u.rol = rol

        # Siempre refresca la contraseña
        u.set_password(password)
        u.save()

        return u, created

    def handle(self, *args, **opts):
        # ------- ADMIN OBLIGATORIO -------
        admin_email = getattr(settings, "BOOTSTRAP_ADMIN_EMAIL", None)
        admin_pass  = getattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", None)
        admin_fn    = getattr(settings, "BOOTSTRAP_ADMIN_FIRST_NAME", "Admin")
        admin_ln    = getattr(settings, "BOOTSTRAP_ADMIN_LAST_NAME", "Demo")

        u, created = self._upsert_user(
            email=admin_email,
            password=admin_pass,
            first_name=admin_fn,
            last_name=admin_ln,
            rol="administrador",
            is_staff=True,
            is_superuser=True,
        )
        if u:
            msg = "CREADO" if created else "ACTUALIZADO"
            self.stdout.write(self.style.SUCCESS(f"[BOOTSTRAP] Admin {msg}: {u.email}"))

        # ------- TÉCNICO OPCIONAL -------
        tech_email = getattr(settings, "BOOTSTRAP_TECH_EMAIL", None)
        tech_pass  = getattr(settings, "BOOTSTRAP_TECH_PASSWORD", None)
        tech_fn    = getattr(settings, "BOOTSTRAP_TECH_FIRST_NAME", "Tec")
        tech_ln    = getattr(settings, "BOOTSTRAP_TECH_LAST_NAME", "Demo")

        if tech_email and tech_pass:
            t, t_created = self._upsert_user(
                email=tech_email,
                password=tech_pass,
                first_name=tech_fn,
                last_name=tech_ln,
                rol="tecnico",
                is_staff=False,
                is_superuser=False,
            )
            if t:
                tmsg = "CREADO" if t_created else "ACTUALIZADO"
                self.stdout.write(self.style.SUCCESS(f"[BOOTSTRAP] Técnico {tmsg}: {t.email}"))
