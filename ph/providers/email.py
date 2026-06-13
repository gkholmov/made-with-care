"""Email escalation channel. SMTP via stdlib; stub logs only (no secrets needed)."""
from __future__ import annotations
import logging
from ph.config import settings

log = logging.getLogger("ph.email")


class EmailSender:
    def send(self, to: str, subject: str, body: str) -> bool:  # pragma: no cover
        raise NotImplementedError


class StubEmail(EmailSender):
    name = "stub"
    sent: list = []  # in-memory record for tests

    def send(self, to: str, subject: str, body: str) -> bool:
        StubEmail.sent.append({"to": to, "subject": subject, "body": body})
        log.info("StubEmail -> %s : %s", to, subject)
        return True


class SMTPEmail(EmailSender):
    name = "smtp"

    def send(self, to: str, subject: str, body: str) -> bool:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(body, _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = to
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as s:
            s.starttls()
            if settings.smtp_user:
                s.login(settings.smtp_user, settings.smtp_password)
            s.sendmail(settings.email_from, [to], msg.as_string())
        return True
