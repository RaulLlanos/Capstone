# core/notify.py
from __future__ import annotations

import logging
import os
from typing import Optional

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .models import Notificacion

log = logging.getLogger(__name__)


def _build_subject_body(notif: Notificacion) -> tuple[str, str]:
    """
    Arma subject/body para EMAIL usando los datos de la asignación + payload.
    Mantiene el formato que ya usabas.
    """
    a = getattr(notif, "asignacion", None)
    p = getattr(notif, "payload", {}) or {}

    asignacion_id = getattr(a, "id", None) or p.get("asignacion_id")
    direccion     = getattr(a, "direccion", "") or p.get("direccion", "")
    comuna        = getattr(a, "comuna", "") or p.get("comuna", "")
    zona          = getattr(a, "zona", "") or p.get("zona", "")
    fecha         = getattr(a, "reagendado_fecha", "") or p.get("reagendado_fecha", "")
    bloque        = getattr(a, "reagendado_bloque", "") or p.get("reagendado_bloque", "")

    # Técnico
    tec_id    = p.get("tecnico_id")
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
        f"Técnico: {tec_nombre or '-'} (id={tec_id or '-'}) {f'| {tec_email}' if tec_email else ''}\n"
    )
    return subject, body


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


def _format_msisdn(num: str) -> Optional[str]:
    """
    Devuelve el msisdn en formato E.164 simple (+569...), o None si no sirve.
    """
    if not num:
        return None
    s = str(num).strip().replace(" ", "")
    if not s.startswith("+"):
        # intenta añadir + si viene sin; puedes ajustar si tu data lo requiere
        if s.startswith("56"):
            s = "+" + s
        elif s.isdigit():
            # No sabemos país → no enviamos
            return None
    return s


def _extract_whatsapp_destination(notif: Notificacion) -> Optional[str]:
    """
    Busca número destino del técnico, sin modificar la DB:
    1) payload.tecnico_msisdn / payload.tecnico_phone
    2) asignacion.asignado_a.telefono / phone (si existe ese campo)
    3) settings.WHATSAPP_TEST_TO (solo para pruebas)
    """
    p = getattr(notif, "payload", {}) or {}
    msisdn = p.get("tecnico_msisdn") or p.get("tecnico_phone")

    if not msisdn:
        asignacion = getattr(notif, "asignacion", None)
        tec = getattr(asignacion, "asignado_a", None)
        # Si tu modelo Usuario no tiene 'telefono', esto simplemente no se usa
        for attr in ("telefono", "phone", "whatsapp"):
            if hasattr(tec, attr):
                msisdn = getattr(tec, attr)
                if msisdn:
                    break

    if not msisdn:
        msisdn = getattr(settings, "WHATSAPP_TEST_TO", "")

    return _format_msisdn(msisdn)


def _build_whatsapp_text(notif: Notificacion) -> str:
    """
    Texto plano que pide el cliente (jerarquía solicitada).
    id tecnico, nombre tecnico, id visita, direccion, comuna, zona,
    nombre cliente, id de la direccion, fecha y bloque.
    """
    a = getattr(notif, "asignacion", None)
    p = getattr(notif, "payload", {}) or {}

    tec_id     = p.get("tecnico_id") or getattr(getattr(a, "asignado_a", None), "id", "")
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

    text = (
        f"Reagendamiento registrado\n"
        f"• Técnico: {tec_nombre or '-'} (id={tec_id or '-'})\n"
        f"• Visita/Asignación: #{visita_id or '-'}\n"
        f"• Dirección: {direccion or '-'}\n"
        f"• Comuna: {comuna or '-'} | Zona: {zona or '-'}\n"
        f"• Cliente: {cliente or '-'} | ID Dirección: {id_dir or '-'}\n"
        f"• Fecha: {fecha or '-'} | Bloque: {bloque or '-'}"
    )
    return text


def _send_whatsapp_cloud(msisdn: str, text: str) -> None:
    """
    Envío básico por WhatsApp Cloud API (texto plano),
    protegido por settings.WHATSAPP_ENABLED.
    NO toca la tabla Notificacion (trazabilidad queda igual que hoy).
    """
    if not getattr(settings, "WHATSAPP_ENABLED", False):
        return

    token = getattr(settings, "WHATSAPP_TOKEN", "")
    phone_id = getattr(settings, "WHATSAPP_PHONE_ID", "")
    if not token or not phone_id:
        log.warning("WhatsApp deshabilitado o sin credenciales; omitiendo envío.")
        return

    url = f"https://graph.facebook.com/v20.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": msisdn,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code >= 400:
            log.error("Error WhatsApp API (%s): %s", resp.status_code, resp.text[:500])
        else:
            log.info("WhatsApp enviado a %s", msisdn)
    except Exception:
        log.exception("Excepción enviando WhatsApp")


def enviar_notificacion_real(notif: Notificacion) -> None:
    """
    Mantenemos envío EMAIL como hoy. Adicionalmente,
    si WHATSAPP_ENABLED=True, se intenta mandar WhatsApp al técnico dueño.
    - No se crea una fila extra en Notificacion para WhatsApp (trazabilidad: intacta).
    """
    subject, body = _build_subject_body(notif)

    # EMAIL (igual que antes)
    _send_email(notif, subject, body)

    # WHATSAPP (queda apagado por flag hasta que lo activen)
    try:
        msisdn = _extract_whatsapp_destination(notif)
        if msisdn:
            _send_whatsapp_cloud(msisdn, _build_whatsapp_text(notif))
    except Exception:
        # No interrumpimos el flujo si WhatsApp falla
        log.exception("Fallo en flujo de WhatsApp opcional")
