from __future__ import annotations

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def _getenv(key: str, default: str = "") -> str:
    v = os.getenv(key)
    return v if v is not None else default

class Command(BaseCommand):
    help = "Crea/actualiza un administrador y (opcional) un técnico usando variables de entorno."

    def handle(self, *args, **options):
        created_any = False

        # ---------- Admin ----------
        admin_email = _getenv("BOOTSTRAP_ADMIN_EMAIL").strip().lower()
        admin_pass  = _getenv("BOOTSTRAP_ADMIN_PASSWORD")
        admin_fn    = _getenv("BOOTSTRAP_ADMIN_FIRST_NAME", "Admin")
        admin_ln    = _getenv("BOOTSTRAP_ADMIN_LAST_NAME", "Bootstrap")

        if admin_email and admin_pass:
            with transaction.atomic():
                user = User.objects.filter(email__iexact=admin_email).first()
                if user:
                    # Actualiza a superuser/admin por si existía mal creado
                    user.first_name = admin_fn
                    user.last_name  = admin_ln
                    user.rol        = "administrador"
                    user.is_staff   = True
                    user.is_superuser = True
                    if admin_pass:
                        user.set_password(admin_pass)
                    user.is_active  = True
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"[OK] Admin actualizado: {admin_email}"))
                else:
                    user = User.objects.create(
                        email=admin_email,
                        first_name=admin_fn,
                        last_name=admin_ln,
                        rol="administrador",
                        is_active=True,
                        is_staff=True,
                        is_superuser=True,
                    )
                    user.set_password(admin_pass)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"[OK] Admin creado: {admin_email}"))
                    created_any = True
        else:
            self.stdout.write("[i] BOOTSTRAP_ADMIN_* no definidos; se omite admin.")

        # ---------- Técnico opcional ----------
        tech_email = _getenv("BOOTSTRAP_TECH_EMAIL").strip().lower()
        tech_pass  = _getenv("BOOTSTRAP_TECH_PASSWORD")
        tech_fn    = _getenv("BOOTSTRAP_TECH_FIRST_NAME", "Tec")
        tech_ln    = _getenv("BOOTSTRAP_TECH_LAST_NAME", "Demo")

        if tech_email and tech_pass:
            with transaction.atomic():
                user = User.objects.filter(email__iexact=tech_email).first()
                if user:
                    user.first_name = tech_fn
                    user.last_name  = tech_ln
                    user.rol        = "tecnico"
                    user.is_staff   = False
                    user.is_superuser = False
                    if tech_pass:
                        user.set_password(tech_pass)
                    user.is_active  = True
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"[OK] Técnico actualizado: {tech_email}"))
                else:
                    user = User.objects.create(
                        email=tech_email,
                        first_name=tech_fn,
                        last_name=tech_ln,
                        rol="tecnico",
                        is_active=True,
                        is_staff=False,
                        is_superuser=False,
                    )
                    user.set_password(tech_pass)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"[OK] Técnico creado: {tech_email}"))
                    created_any = True
        else:
            self.stdout.write("[i] BOOTSTRAP_TECH_* no definidos; se omite técnico.")

        if not created_any:
            self.stdout.write(self.style.WARNING("[i] Bootstrap no creó usuarios nuevos (puede haber actualizado existentes)."))
