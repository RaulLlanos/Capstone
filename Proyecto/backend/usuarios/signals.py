# usuarios/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Usuario

@receiver(pre_save, sender=Usuario)
def ensure_staff_for_admin_role(sender, instance: Usuario, **kwargs):
    # Promueve a staff si es administrador
    if getattr(instance, "rol", None) == "administrador":
        instance.is_staff = True
    # Si quieres “degradar” cuando pasa a técnico, descomenta:
    # else:
    #     instance.is_staff = False
