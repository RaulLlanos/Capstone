# auditoria/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import AuditoriaVisita

@receiver(pre_save, sender=AuditoriaVisita)
def auditoria_pre_save(sender, instance, **kwargs):
    # Placeholder: aquí puedes validar skip-logic, etc.
    # Por ahora no hace nada, solo evita el ImportError.
    pass
