# auditoria/signals.py
from __future__ import annotations

from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuditoriaVisita, EstadoCliente
from asignaciones.models import HistorialAsignacion, DireccionAsignada
from core.models import Notificacion
from core.notify import (
    enviar_notificacion_background,
    enviar_notificacion_whatsapp_background,
)


def _accion(name: str):
    # Devuelve enum si existe, o string como fallback
    try:
        return getattr(HistorialAsignacion.Accion, name)
    except Exception:
        return name


def _bloque_label(b):
    return "10:00 a 13:00" if b == "10-13" else ("14:00 a 18:00" if b == "14-18" else (b or "-"))


def _notify_reagendo_async(asign: DireccionAsignada, dest_user, fecha, bloque):
    """
    Crea Notificacion y la envía en background (email y opcional WhatsApp).
    Se ejecuta DESPUÉS del commit de la transacción.
    """
    tec_nombre = f"{(getattr(dest_user, 'first_name', '') or '').strip()} {(getattr(dest_user, 'last_name', '') or '').strip()}".strip() or (getattr(dest_user, 'email', '') or '')

    payload = {
        # técnico primero (contrato claro)
        "tecnico_id": getattr(dest_user, "id", None),
        "tecnico_nombre": tec_nombre,
        "tecnico_email": getattr(dest_user, "email", "") or "",

        # visita
        "asignacion_id": getattr(asign, "id", None),
        "direccion": getattr(asign, "direccion", ""),
        "comuna": getattr(asign, "comuna", ""),
        "zona": getattr(asign, "zona", ""),

        # cliente (si lo tienes en el modelo)
        "cliente_nombre": getattr(asign, "nombre_cliente", "") or "",
        "id_vivienda": getattr(asign, "id_vivienda", "") or "",

        # reagendo
        "reagendado_fecha": str(fecha),
        "reagendado_bloque": bloque,
    }

    # EMAIL (si hay destino)
    notif_email = Notificacion.objects.create(
        tipo="reagendo",
        asignacion=asign,
        canal=Notificacion.Canal.EMAIL if (getattr(dest_user, "email", "") or "").strip() else Notificacion.Canal.NONE,
        destino=(getattr(dest_user, "email", "") or "").strip(),
        provider="",
        payload=payload,
        status=Notificacion.Estado.QUEUED,
    )
    enviar_notificacion_background(notif_email)

    # WHATSAPP (si está habilitado y tenemos teléfono)
    phone = None
    for attr in ("telefono", "phone", "whatsapp"):
        if hasattr(dest_user, attr):
            phone = getattr(dest_user, attr)
            if phone:
                break

    if getattr(settings, "WHATSAPP_ENABLED", False) and phone:
        notif_wsp = Notificacion.objects.create(
            tipo="reagendo",
            asignacion=asign,
            canal=Notificacion.Canal.WEBHOOK,  # usamos WEBHOOK como canal de “salida” a WA
            destino=str(phone),
            provider="",
            payload=payload,
            status=Notificacion.Estado.QUEUED,
        )
        enviar_notificacion_whatsapp_background(notif_wsp, to_msisdn=str(phone))


@receiver(post_save, sender=AuditoriaVisita)
def auditoria_side_effects(sender, instance: AuditoriaVisita, created, **kwargs):
    """
    Al crear una auditoría:
      - Si customer_status=REAGENDA y tiene fecha/bloque -> actualiza Asignación, loguea REAGENDADA y notifica en background.
      - Si customer_status=AUTORIZA -> loguea CERRADA.
      - En otros estados -> loguea ESTADO_CLIENTE.
    (Se mantienen nombres/contratos existentes.)
    """
    if not created:
        return

    asign = instance.asignacion
    user = instance.tecnico  # puede ser None si lo creó un admin

    if instance.customer_status == EstadoCliente.REAGENDA:
        if instance.reschedule_date and instance.reschedule_slot:
            old_fecha = getattr(asign, "reagendado_fecha", None)
            old_bloque = getattr(asign, "reagendado_bloque", None)

            # Si estaba PENDIENTE puedes mantener tu criterio; aquí no forzamos ORIENTE/SUR/NORTE (no se toca).
            # Estado: opcionalmente dejar REAGENDADA o mantener tu flujo. Tu código original marcaba REAGENDADA.
            if hasattr(asign, "estado"):
                asign.reagendado_fecha = instance.reschedule_date
                asign.reagendado_bloque = instance.reschedule_slot
                asign.estado = "REAGENDADA"
                asign.save(update_fields=["reagendado_fecha", "reagendado_bloque", "estado"])
            else:
                asign.reagendado_fecha = instance.reschedule_date
                asign.reagendado_bloque = instance.reschedule_slot
                asign.save(update_fields=["reagendado_fecha", "reagendado_bloque"])

            HistorialAsignacion.objects.create(
                asignacion=asign,
                accion=_accion("REAGENDADA"),
                detalles=f"Reagendada desde auditoría: {old_fecha or '-'} {_bloque_label(old_bloque)} -> {instance.reschedule_date} {_bloque_label(instance.reschedule_slot)}",
                usuario=user,
            )

            # Notificación ASÍNCRONA después del commit (no bloquea el request)
            dest_user = user if user else getattr(asign, "asignado_a", None)
            if dest_user:
                def _on_commit():
                    _notify_reagendo_async(asign, dest_user, instance.reschedule_date, instance.reschedule_slot)
                transaction.on_commit(_on_commit)

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
