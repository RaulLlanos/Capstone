from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Crea o actualiza un admin y (opcional) un técnico desde variables de entorno BOOTSTRAP_*."

    def handle(self, *args, **kwargs):
        # Admin obligatorio
        email = getattr(settings, "BOOTSTRAP_ADMIN_EMAIL", None)
        password = getattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", None)
        first = getattr(settings, "BOOTSTRAP_ADMIN_FIRST_NAME", "Admin")
        last = getattr(settings, "BOOTSTRAP_ADMIN_LAST_NAME", "User")

        if not email or not password:
            self.stdout.write(self.style.WARNING("BOOTSTRAP_ADMIN_* no definidas. Omitiendo admin."))
        else:
            user, created = User.objects.get_or_create(email__iexact=email, defaults={
                "email": email,
                "first_name": first,
                "last_name": last,
                "rol": "administrador",
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            })
            # Asegura flags y password aunque ya exista
            user.first_name = first
            user.last_name = last
            user.rol = "administrador"
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Admin {'creado' if created else 'actualizado'}: {email}"
            ))

        # Técnico opcional
        tech_email = getattr(settings, "BOOTSTRAP_TECH_EMAIL", None)
        tech_password = getattr(settings, "BOOTSTRAP_TECH_PASSWORD", None)
        tech_first = getattr(settings, "BOOTSTRAP_TECH_FIRST_NAME", "Tec")
        tech_last = getattr(settings, "BOOTSTRAP_TECH_LAST_NAME", "User")

        if tech_email and tech_password:
            t, created = User.objects.get_or_create(email__iexact=tech_email, defaults={
                "email": tech_email,
                "first_name": tech_first,
                "last_name": tech_last,
                "rol": "tecnico",
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            })
            t.first_name = tech_first
            t.last_name = tech_last
            t.rol = "tecnico"
            t.is_active = True
            t.is_staff = False
            t.is_superuser = False
            t.set_password(tech_password)
            t.save()
            self.stdout.write(self.style.SUCCESS(
                f"Técnico {'creado' if created else 'actualizado'}: {tech_email}"
            ))
        else:
            self.stdout.write("Sin BOOTSTRAP_TECH_*. Omitiendo técnico.")
