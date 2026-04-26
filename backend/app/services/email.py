"""Cliente SMTP simple. Devuelve True/False, nunca lanza al caller."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        logger.debug(f"Email deshabilitado — no se envía a {to}")
        return False

    if not settings.SMTP_HOST or not to:
        logger.warning("SMTP no configurado o destinatario vacío — email omitido.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        if settings.SMTP_USE_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.starttls()
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        logger.info(f"Email enviado a {to}: {subject}")
        return True
    except Exception as exc:
        logger.error(f"Error enviando email a {to}: {exc}")
        return False
