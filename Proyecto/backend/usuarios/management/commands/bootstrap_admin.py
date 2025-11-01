from __future__ import annotations

import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def _upsert_user(email: str, password: str, first: str, last: str, rol: str,
                 is_superuser: bool, is_staff: bool) -> User:
    u = User.objects.filter(email__iexact=email).first()
    if u is None:
        u = User(email=email)
    u.first_name = first or u.first_name
    u.last_name = last or u.last_name
    u.rol = rol or getattr(u, "rol", "tecnico")
    u.is_active = True
    u.is_staff = is_staff
    u.is_superuser = is_superuser
    if password:
        u.set_password(password)
    u.save()
    return u

class Command(BaseCommand):
    help = "Crea/actualiza usuario admin (y opcionalmente técnico) desde variables de entorno."

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip()
                admin_pass = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "").strip()
                admin_fn   = os.getenv("BOOTSTRAP_ADMIN_FIRST_NAME", "Admin").strip()
                admin_ln   = os.getenv("BOOTSTRAP_ADMIN_LAST_NAME", "Demo").strip()

                if not admin_email or not admin_pass:
                    raise CommandError("Faltan BOOTSTRAP_ADMIN_EMAIL o BOOTSTRAP_ADMIN_PASSWORD.")

                admin = _upsert_user(
                    email=admin_email,
                    password=admin_pass,
                    first=admin_fn,
                    last=admin_ln,
                    rol="administrador",
                    is_superuser=True,
                    is_staff=True,
                )
                self.stdout.write(self.style.SUCCESS(f"Admin listo: {admin.email} (id={admin.id})"))

                # Técnico opcional
                tech_email = os.getenv("BOOTSTRAP_TECH_EMAIL", "").strip()
                tech_pass  = os.getenv("BOOTSTRAP_TECH_PASSWORD", "").strip()
                tech_fn    = os.getenv("BOOTSTRAP_TECH_FIRST_NAME", "Tec").strip()
                tech_ln    = os.getenv("BOOTSTRAP_TECH_LAST_NAME", "Demo").strip()

                if tech_email and tech_pass:
                    tech = _upsert_user(
                        email=tech_email,
                        password=tech_pass,
                        first=tech_fn,
                        last=tech_ln,
                        rol="tecnico",
                        is_superuser=False,
                        is_staff=False,
                    )
                    self.stdout.write(self.style.SUCCESS(f"Técnico listo: {tech.email} (id={tech.id})"))

        except Exception as e:
            raise CommandError(str(e))
