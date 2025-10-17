# core/notify.py
from dataclasses import dataclass
from typing import List, Tuple
from django.core.mail import EmailMultiAlternatives

@dataclass
class SendResult:
    ok: bool
    provider: str
    message_id: str | None
    error: str | None

# --- Adapter: SMTP (Gmail u otro) ---
def _smtp_send(subject: str, body: str, to_list: List[str], from_email: str) -> SendResult:
    try:
        msg = EmailMultiAlternatives(subject, body, from_email, to_list)
        msg.send(fail_silently=False)
        # Django no expone message_id del proveedor; dejamos None
        return SendResult(True, "smtp", None, None)
    except Exception as e:
        return SendResult(False, "smtp", None, str(e)[:1000])

# --- Adapter: placeholder SendGrid (para futuro) ---
def _sendgrid_send(subject: str, body: str, to_list: List[str], from_email: str) -> SendResult:
    # Ejemplo para migrar a API de SendGrid/Mailgun/SES cuando lo necesites
    return SendResult(False, "sendgrid", None, "Adapter no implementado")

def send_email(subject: str, body: str, to_list: List[str], from_email: str) -> Tuple[bool, str, str | None, str | None]:
    """
    Fachada simple: permite cambiar el proveedor sin tocar el resto del código.
    Por ahora usamos SMTP directamente (la selección del backend se hace en settings).
    """
    if not to_list:
        return False, "none", None, "Sin destinatarios"

    # Hoy: enviamos con SMTP; si luego implementas SendGrid, cámbialo aquí.
    res = _smtp_send(subject, body, to_list, from_email)
    return res.ok, res.provider, res.message_id, res.error
