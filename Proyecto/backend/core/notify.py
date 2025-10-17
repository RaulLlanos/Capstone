# core/notify.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from core.models import Notificacion


def _build_subject_body(notif):
    """
    Arma subject y body del correo en base a la notificación.
    """
    a = getattr(notif, "asignacion", None)
    p = notif.payload or {}
    tipo = notif.tipo or "evento"

    asignacion_id = getattr(a, "id", "N/A")
    direccion = getattr(a, "direccion", "") or p.get("direccion", "")
    comuna = getattr(a, "comuna", "") or p.get("comuna", "")

    subject = f"[{tipo}] Asignación #{asignacion_id}"

    lines = [
        f"Tipo: {tipo}",
        f"Asignación: #{asignacion_id}",
        f"Dirección: {direccion}",
        f"Comuna: {comuna}",
    ]

    # Datos de reagendo si vienen en payload
    if "reagendado_fecha" in p:
        lines.append(f"Fecha reagendada: {p.get('reagendado_fecha', '')}")
    if "reagendado_bloque" in p:
        lines.append(f"Bloque: {p.get('reagendado_bloque', '')}")

    # Datos del técnico (si vienen)
    if "tecnico_id" in p:
        lines.append(f"Técnico ID: {p.get('tecnico_id', '')}")
    if "tecnico_email" in p:
        lines.append(f"Técnico email: {p.get('tecnico_email', '')}")

    body = "\n".join(lines)
    return subject, body


def enviar_notificacion_real(notif: Notificacion) -> None:
    """
    Envía un email real usando el backend SMTP configurado en settings.py.
    Marca la notificación como SENT o FAILED y setea provider='smtp'.
    También copia a settings.NOTIFY_ADMIN_EMAILS si está configurado.

    No raisea excepción hacia arriba; si falla, actualiza la notificación a FAILED.
    """
    # Destinatarios: el destino de la notificación + copias
    to_list = []
    if notif.destino:
        to_list.append(notif.destino)

    # Copias a administradores (opcional, puede estar vacío)
    notify_copies = getattr(settings, "NOTIFY_ADMIN_EMAILS", [])
    if isinstance(notify_copies, (list, tuple)):
        to_list += [e for e in notify_copies if e]
    elif isinstance(notify_copies, str) and notify_copies.strip():
        to_list.append(notify_copies.strip())

    # Si no hay nadie a quién enviar, no hacemos nada (queda en cola)
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
        # Si usas EMAIL_BACKEND=console en dev, igual “envía” y marca SENT.
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
