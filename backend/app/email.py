"""Email delivery. Uses SMTP when configured; otherwise logs the message so
password-reset links are still retrievable in a no-email pilot environment.
"""
import smtplib
import ssl
from email.message import EmailMessage

from .config import settings


def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.SMTP_HOST:
        print(
            f"[email] (no SMTP configured) to={to!r} subject={subject!r}\n"
            f"------\n{body}\n------"
        )
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls(context=ssl.create_default_context())
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[email] send to {to} failed: {exc}")
        return False
