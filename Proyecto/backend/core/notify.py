# core/notify.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from core.models import Notificacion

def _build_subject_body(notif: Notificacion) -> tuple[str, str]:
    a = notif.asignacion
    p = notif.payload or {}
    tipo = notif.tipo or "evento"

    subject = f"[{tipo}] Asignación #{getattr(a, 'id', 'N/A')}"
    body = (
        f"Tipo: {tipo}\n"
        f"Asignación: #{getattr(a, 'id', 'N/A')}\n"
        f"Dirección: {getattr(a, 'direccion', '')}\n"
        f"Comuna: {getattr(a, 'comuna', '')}\n"
        f"Fecha reagendada: {p.get('reagendado_fecha', '')}\n"
        f"Bloque: {p.get('reagendado_bloque', '')}\n"
        f"Técnico ID: {p.get('tecnico_id', '')}\n"
        f"Técnico email: {p.get('tecnico_email', '')}\n"
    )
    return subject, body

def enviar_notificacion_real(notif: Notificacion):
    """
    Envía email real usando el backend SMTP configurado.
    Marca la notificación como SENT/FAILED y setea provider='smtp'.
    """
    to_list = []
    if notif.destino:
        to_list.append(notif.destino)
    to_list += getattr(settings, "NOTIFY_ADMIN_EMAILS", [])

    # Si no hay destino, no intentamos envío (solo dejamos en cola)
    if not to_list:
        return

    subject, body = _build_subject_body(notif)
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@localhost"),
            to=to_list,
        )
        msg.send(fail_silently=False)
        notif.provider = "smtp"
        notif.status = Notificacion.Estado.SENT
        notif.sent_at = timezone.now()
        notif.save(update_fields=["provider", "status", "sent_at"])
    except Exception as e:
        notif.provider = "smtp"
        notif.status = Notificacion.Estado.FAILED
        notif.error = (str(e)[:1000] if e else "Error desconocido")
        notif.save(update_fields=["provider", "status", "error"])
