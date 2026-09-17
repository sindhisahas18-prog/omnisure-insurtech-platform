"""
Email notifications. Sends for real via SMTP when EMAIL_SMTP_* is
configured; otherwise logs the would-be email (DEMO MODE) instead of
silently doing nothing or crashing, per the spec's "app must still
launch, use a clearly marked DEMO MODE fallback" rule.
"""

import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("omnisure.email")


def send_email(to: str, subject: str, body: str) -> dict:
    """Returns {"sent": bool, "demo_mode": bool, "error": str|None}."""
    if not (settings.EMAIL_SMTP_HOST and settings.EMAIL_SMTP_USER and settings.EMAIL_SMTP_PASSWORD):
        logger.info("[DEMO MODE — email not sent] To: %s | Subject: %s | Body: %s", to, subject, body)
        return {"sent": False, "demo_mode": True, "error": None}

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_SMTP_USER
        msg["To"] = to

        with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT or 587) as server:
            server.starttls()
            server.login(settings.EMAIL_SMTP_USER, settings.EMAIL_SMTP_PASSWORD)
            server.send_message(msg)
        return {"sent": True, "demo_mode": False, "error": None}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Email send failed, falling back to demo log: %s", exc)
        logger.info("[DEMO MODE — email not sent] To: %s | Subject: %s | Body: %s", to, subject, body)
        return {"sent": False, "demo_mode": True, "error": str(exc)}
