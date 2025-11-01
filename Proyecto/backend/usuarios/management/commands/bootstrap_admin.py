import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

def _upsert_user(email, password, first_name, last_name, rol, is_staff=False, is_superuser=False):
    email = (email or "").strip().lower()
    if not email or not password:
        return None, False

    user = User.objects.filter(email__iexact=email).first()
    if user:
        user.first_name = first_name or user.first_name
        user.last_name  = last_name or user.last_name
        if hasattr(user, "rol") and rol:
            user.rol = rol
        user.is_active = True
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()
        return user, False
    else:
        data = {
            "email": email,
            "first_name": first_name or "",
            "last_name": last_name or "",
            "is_active": True,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
        }
        if "rol" in [f.name for f in User._meta.get_fields()]:
            data["rol"] = rol
        user = User.objects.create(**data)
        user.set_password(password)
        user.save()
        return user, True

class Command(BaseCommand):
    help = "Crea/actualiza un administrador y (opcional) un técnico desde variables BOOTSTRAP_*"

    def handle(self, *args, **opts):
        # --- Admin (obligatorio) ---
        a_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
        a_pass  = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
        a_fn    = os.environ.get("BOOTSTRAP_ADMIN_FIRST_NAME", "Admin")
        a_ln    = os.environ.get("BOOTSTRAP_ADMIN_LAST_NAME", "Demo")

        if a_email and a_pass:
            admin, created = _upsert_user(
                email=a_email, password=a_pass,
                first_name=a_fn, last_name=a_ln,
                rol="administrador", is_staff=True, is_superuser=True,
            )
            if admin:
                self.stdout.write(self.style.SUCCESS(
                    f"Admin listo: {admin.email} (created={created})"
                ))
        else:
            self.stdout.write(self.style.WARNING(
                "BOOTSTRAP_ADMIN_EMAIL / BOOTSTRAP_ADMIN_PASSWORD no definidos; omitiendo admin."
            ))

        # --- Técnico (opcional) ---
        t_email = os.environ.get("BOOTSTRAP_TECH_EMAIL")
        t_pass  = os.environ.get("BOOTSTRAP_TECH_PASSWORD")
        t_fn    = os.environ.get("BOOTSTRAP_TECH_FIRST_NAME", "Tec")
        t_ln    = os.environ.get("BOOTSTRAP_TECH_LAST_NAME", "Demo")

        if t_email and t_pass:
            tech, created = _upsert_user(
                email=t_email, password=t_pass,
                first_name=t_fn, last_name=t_ln,
                rol="tecnico", is_staff=False, is_superuser=False,
            )
            if tech:
                self.stdout.write(self.style.SUCCESS(
                    f"Técnico listo: {tech.email} (created={created})"
                ))
        # idempotente: si ya existen, actualiza nombres/rol/flags y resetea la clave
