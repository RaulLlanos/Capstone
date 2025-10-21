from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AuditoriaVisita, EstadoCliente
from asignaciones.models import HistorialAsignacion

def _accion(name: str):
    # Devuelve enum si existe, o string como fallback
    try:
        return getattr(HistorialAsignacion.Accion, name)
    except Exception:
        return name

@receiver(post_save, sender=AuditoriaVisita)
def auditoria_side_effects(sender, instance: AuditoriaVisita, created, **kwargs):
    """
    Al crear una auditoría:
      - Si customer_status=REAGENDA y tiene fecha/bloque -> actualiza Asignación y loguea REAGENDADA
      - Si customer_status=AUTORIZA -> loguea CERRADA
      - En otros estados -> loguea ESTADO_CLIENTE
    """
    if not created:
        return

    asign = instance.asignacion
    user = instance.tecnico  # puede ser None si lo creó un admin

    if instance.customer_status == EstadoCliente.REAGENDA:
        if instance.reschedule_date and instance.reschedule_slot:
            # Actualiza reagendo en Asignación
            asign.reagendado_fecha = instance.reschedule_date
            asign.reagendado_bloque = instance.reschedule_slot
            # Si tu modelo DireccionAsignada tiene campo 'estado', lo marcamos.
            if hasattr(asign, "estado"):
                asign.estado = "REAGENDADA"
                asign.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado"])
            else:
                asign.save(update_fields=["reagendado_fecha", "reagendado_bloque"])

            HistorialAsignacion.objects.create(
                asignacion=asign,
                accion=_accion("REAGENDADA"),
                detalles=f"Reagendada desde auditoría a {instance.reschedule_date} {instance.reschedule_slot}",
                usuario=user,
            )

    elif instance.customer_status == EstadoCliente.AUTORIZA:
        HistorialAsignacion.objects.create(
            asignacion=asign,
            accion=_accion("CERRADA"),
            detalles="Auditoría: cliente autorizó el trabajo. Marcada como visitada/cerrada.",
            usuario=user,
        )
    else:
        HistorialAsignacion.objects.create(
            asignacion=asign,
            accion=_accion("ESTADO_CLIENTE"),
            detalles=f"Auditoría: estado_cliente={instance.customer_status}.",
            usuario=user,
        )
