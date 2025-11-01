from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = "Crea o actualiza un usuario administrador (y opcionalmente un técnico) desde variables BOOTSTRAP_*"

    def handle(self, *args, **opts):
        # --- Admin obligatorio ---
        admin_email = getattr(settings, "BOOTSTRAP_ADMIN_EMAIL", None)
        admin_pass  = getattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", None)
        admin_fn    = getattr(settings, "BOOTSTRAP_ADMIN_FIRST_NAME", "Admin")
        admin_ln    = getattr(settings, "BOOTSTRAP_ADMIN_LAST_NAME", "Demo")

        if admin_email and admin_pass:
            admin, created = User.objects.get_or_create(email__iexact=admin_email, defaults={
                "email": admin_email,
                "first_name": admin_fn,
                "last_name": admin_ln,
                "rol": "administrador",
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            })
            # Normaliza si vino por email__iexact
            if not created and admin.email != admin_email:
                admin.email = admin_email

            # Asegura flags y nombre
            admin.first_name  = admin_fn
            admin.last_name   = admin_ln
            admin.rol         = "administrador"
            admin.is_active   = True
            admin.is_staff    = True
            admin.is_superuser= True

            # Setea/actualiza password
            admin.set_password(admin_pass)
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Admin listo: {admin.email} (created={created})"))
        else:
            self.stdout.write(self.style.WARNING("BOOTSTRAP_ADMIN_EMAIL/BOOTSTRAP_ADMIN_PASSWORD no definidos; omitiendo admin."))

        # --- Técnico opcional ---
        tech_email = getattr(settings, "BOOTSTRAP_TECH_EMAIL", None)
        tech_pass  = getattr(settings, "BOOTSTRAP_TECH_PASSWORD", None)
        tech_fn    = getattr(settings, "BOOTSTRAP_TECH_FIRST_NAME", "Tec")
        tech_ln    = getattr(settings, "BOOTSTRAP_TECH_LAST_NAME", "Demo")

        if tech_email and tech_pass:
            tech, created = User.objects.get_or_create(email__iexact=tech_email, defaults={
                "email": tech_email,
                "first_name": tech_fn,
                "last_name": tech_ln,
                "rol": "tecnico",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            })
            if not created and tech.email != tech_email:
                tech.email = tech_email

            tech.first_name = tech_fn
            tech.last_name  = tech_ln
            tech.rol        = "tecnico"
            tech.is_active  = True
            tech.is_staff   = False
            tech.is_superuser = False

            tech.set_password(tech_pass)
            tech.save()
            self.stdout.write(self.style.SUCCESS(f"Técnico listo: {tech.email} (created={created})"))
