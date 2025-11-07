# core/notify.py
from __future__ import annotations

import logging
import threading
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .models import Notificacion

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de armado de mensajes
# ---------------------------------------------------------------------------
def _build_subject_body(notif: Notificacion) -> tuple[str, str]:
    """
    Arma subject/body para EMAIL usando los datos de la asignación + payload.
    """
    a = getattr(notif, "asignacion", None)
    p = getattr(notif, "payload", {}) or {}

    asignacion_id = getattr(a, "id", None) or p.get("asignacion_id")
    direccion     = getattr(a, "direccion", "") or p.get("direccion", "")
    comuna        = getattr(a, "comuna", "") or p.get("comuna", "")
    zona          = getattr(a, "zona", "") or p.get("zona", "")
    fecha         = getattr(a, "reagendado_fecha", "") or p.get("reagendado_fecha", "")
    bloque        = getattr(a, "reagendado_bloque", "") or p.get("reagendado_bloque", "")

    # Técnico (desde payload si lo envías; si no, queda vacío)
    tec_id     = p.get("tecnico_id")
    tec_nombre = p.get("tecnico_nombre") or ""
    tec_email  = p.get("tecnico_email") or ""

    # Cliente
    cliente_nombre = p.get("cliente_nombre") or ""
    cliente_rut    = p.get("cliente_rut") or getattr(a, "rut_cliente", "")

    subject = f"[{notif.tipo.upper()}] Asignación #{asignacion_id}"
    body = (
        f"Asignación #{asignacion_id}\n"
        f"Dirección: {direccion}\n"
        f"Comuna: {comuna} | Zona: {zona}\n"
        f"Cliente: {cliente_nombre or '-'} | RUT: {cliente_rut or '-'}\n"
        f"Fecha: {fecha or '-'} | Bloque: {bloque or '-'}\n"
        f"\n"
        f"Técnico: {tec_nombre or '-'} (id={tec_id or '-'})"
        f"{(' | ' + tec_email) if tec_email else ''}\n"
    )
    return subject, body


def _build_whatsapp_text(notif: Notificacion) -> str:
    """
    Texto plano para WhatsApp con la jerarquía solicitada:
    id técnico, nombre técnico, id visita, dirección, comuna, zona,
    nombre cliente, id de la dirección, fecha y bloque.
    """
    a = getattr(notif, "asignacion", None)
    p = getattr(notif, "payload", {}) or {}

    tec_id = p.get("tecnico_id") or getattr(getattr(a, "asignado_a", None), "id", "")
    tec_nombre = p.get("tecnico_nombre") or (
        f"{getattr(getattr(a, 'asignado_a', None), 'first_name', '')} "
        f"{getattr(getattr(a, 'asignado_a', None), 'last_name', '')}"
    ).strip()

    visita_id  = getattr(a, "id", None) or p.get("asignacion_id")
    direccion  = getattr(a, "direccion", "") or p.get("direccion", "")
    comuna     = getattr(a, "comuna", "") or p.get("comuna", "")
    zona       = getattr(a, "zona", "") or p.get("zona", "")
    cliente    = p.get("cliente_nombre") or ""
    id_dir     = getattr(a, "id_vivienda", "") or p.get("id_vivienda", "")
    fecha      = getattr(a, "reagendado_fecha", "") or p.get("reagendado_fecha", "")
    bloque     = getattr(a, "reagendado_bloque", "") or p.get("reagendado_bloque", "")

    return (
        "Reagendamiento registrado\n"
        f"• Técnico: {tec_nombre or '-'} (id={tec_id or '-'})\n"
        f"• Visita/Asignación: #{visita_id or '-'}\n"
        f"• Dirección: {direccion or '-'}\n"
        f"• Comuna: {comuna or '-'} | Zona: {zona or '-'}\n"
        f"• Cliente: {cliente or '-'} | ID Dirección: {id_dir or '-'}\n"
        f"• Fecha: {fecha or '-'} | Bloque: {bloque or '-'}"
    )


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def _send_email(notif: Notificacion, subject: str, body: str) -> None:
    """
    Envía EMAIL si notif.canal==EMAIL y hay destino.
    Actualiza provider/status/sent_at en éxito o error.
    """
    if notif.canal != Notificacion.Canal.EMAIL or not notif.destino:
        return

    msg = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[notif.destino],
    )
    try:
        msg.send(fail_silently=False)
        notif.provider = "smtp"
        notif.status = Notificacion.Estado.SENT
        notif.sent_at = timezone.now()
        notif.save(update_fields=["provider", "status", "sent_at", "updated_at"])
    except Exception as e:
        notif.provider = "smtp"
        notif.status = Notificacion.Estado.FAILED
        notif.error = str(e)[:500]
        notif.save(update_fields=["provider", "status", "error", "updated_at"])
        log.exception("Fallo envío EMAIL para Notificacion #%s", notif.id)


# ---------------------------------------------------------------------------
# WhatsApp (Cloud API) — sólo para el técnico dueño, no modifica trazabilidad
# ---------------------------------------------------------------------------
def _format_msisdn(num: str) -> Optional[str]:
    """Normaliza a E.164 simple (+569...). Devuelve None si no es usable."""
    if not num:
        return None
    s = str(num).strip().replace(" ", "")
    if not s.startswith("+"):
        if s.startswith("56"):
            s = "+" + s
        elif s.isdigit():
            return None
    return s


def _extract_whatsapp_destination(notif: Notificacion) -> Optional[str]:
    """
    Obtiene el número del TÉCNICO dueño, sin tocar la DB:
    1) payload.tecnico_msisdn / payload.tecnico_phone
    2) asignacion.asignado_a.telefono/phone/whatsapp (si existiera ese campo)
    3) settings.WHATSAPP_TEST_TO (sólo pruebas)
    """
    p = getattr(notif, "payload", {}) or {}
    msisdn = p.get("tecnico_msisdn") or p.get("tecnico_phone")

    if not msisdn:
        asignacion = getattr(notif, "asignacion", None)
        tec = getattr(asignacion, "asignado_a", None)
        for attr in ("telefono", "phone", "whatsapp"):
            if hasattr(tec, attr):
                msisdn = getattr(tec, attr)
                if msisdn:
                    break

    if not msisdn:
        msisdn = getattr(settings, "WHATSAPP_TEST_TO", "")

    return _format_msisdn(msisdn)


def _send_whatsapp_cloud(msisdn: str, text: str) -> None:
    """
    Envío básico por WhatsApp Cloud API (texto plano).
    Protegido por settings.WHATSAPP_ENABLED. No modifica Notificacion.
    """
    if not getattr(settings, "WHATSAPP_ENABLED", False):
        return

    token = getattr(settings, "WHATSAPP_TOKEN", "")
    phone_id = getattr(settings, "WHATSAPP_PHONE_ID", "")
    if not token or not phone_id:
        log.warning("WhatsApp sin credenciales; omitiendo envío.")
        return

    # Import local para no romper si 'requests' no está instalado en entornos mínimos
    try:
        import requests  # type: ignore
    except Exception as e:
        log.warning("requests no disponible; omitiendo WhatsApp. %s", e)
        return

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": msisdn,
        "type": "text",
        "text": {"body": text, "preview_url": False},
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code >= 400:
            log.error("Error WhatsApp API (%s): %s", resp.status_code, resp.text[:500])
        else:
            log.info("WhatsApp enviado a %s", msisdn)
    except Exception:
        log.exception("Excepción enviando WhatsApp")


# ---------------------------------------------------------------------------
# API pública usada por las vistas
# ---------------------------------------------------------------------------
def enviar_notificacion_real(notif: Notificacion) -> None:
    """
    Mantiene el EMAIL como hoy.
    Además, si WHATSAPP_ENABLED=True, intenta mandar WhatsApp al técnico dueño.
    (No crea filas extra en Notificacion; tu trazabilidad queda intacta).
    """
    subject, body = _build_subject_body(notif)

    # EMAIL (igual que antes)
    _send_email(notif, subject, body)

    # WHATSAPP opcional (no rompe si está desactivado)
    try:
        msisdn = _extract_whatsapp_destination(notif)
        if msisdn:
            _send_whatsapp_cloud(msisdn, _build_whatsapp_text(notif))
    except Exception:
        log.exception("Fallo en flujo de WhatsApp opcional")


def enviar_notificacion_whatsapp(notif: Notificacion, *, to_msisdn: Optional[str] = None) -> None:
    """
    Stub solicitado por vistas:
    - Si WhatsApp está desactivado, no hace nada.
    - Envía SOLO al técnico dueño (o 'to_msisdn' si lo pasas).
    - No modifica la fila Notificacion (trazabilidad queda como hoy).
    """
    try:
        msisdn = _format_msisdn(to_msisdn) if to_msisdn else _extract_whatsapp_destination(notif)
        if msisdn:
            _send_whatsapp_cloud(msisdn, _build_whatsapp_text(notif))
    except Exception:
        log.exception("Fallo en stub enviar_notificacion_whatsapp")


# ---------------------------------------------------------------------------
# Wrappers en background (no bloquean el request)
# ---------------------------------------------------------------------------
def enviar_notificacion_background(notif: Notificacion) -> None:
    """Dispara enviar_notificacion_real en un thread (daemon)."""
    threading.Thread(target=enviar_notificacion_real, args=(notif,), daemon=True).start()


def enviar_notificacion_whatsapp_background(notif: Notificacion, *, to_msisdn: Optional[str] = None) -> None:
    """Dispara enviar_notificacion_whatsapp en un thread (daemon)."""
    threading.Thread(
        target=enviar_notificacion_whatsapp,
        kwargs={"notif": notif, "to_msisdn": to_msisdn},
        daemon=True,
    ).start()
