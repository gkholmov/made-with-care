"""Relative escalation — fan out to Telegram + email (MVP channels).

`telegram_send` is injected (a function that sends a TG message to a chat id) so
this module has no hard dependency on the bot runtime and is easy to test.
"""
from __future__ import annotations
import logging
from typing import Callable, Optional
from ph.core.i18n import RELATIVE_NOTICE
from ph.db import store

log = logging.getLogger("ph.notify")


class Notifier:
    def __init__(self, telegram_send: Optional[Callable[[int, str], bool]] = None, email=None):
        self.telegram_send = telegram_send
        self.email = email

    def escalate(self, elder_name: str, reason: str, relative, event_id: Optional[int] = None) -> list[str]:
        """Notify the trusted relative on every available channel. Returns channels used."""
        if not relative:
            log.warning("escalate: no trusted relative linked")
            return []
        lang = getattr(relative, "language", "en") or "en"
        msg = RELATIVE_NOTICE.get(lang, RELATIVE_NOTICE["en"]).format(
            elder=elder_name or "your relative", reason=reason)
        used = []
        # Telegram
        if self.telegram_send and getattr(relative, "telegram_id", None):
            try:
                self.telegram_send(relative.telegram_id, msg)
                store.log_notification(relative.id, "telegram", event_id, "sent")
                used.append("telegram")
            except Exception as e:  # pragma: no cover
                store.log_notification(relative.id, "telegram", event_id, "failed")
                log.error("telegram notify failed: %s", e)
        # Email
        if self.email and getattr(relative, "email", ""):
            ok = False
            try:
                ok = self.email.send(relative.email, "Your relative needs a hand", msg)
            except Exception as e:  # pragma: no cover
                log.error("email notify failed: %s", e)
            store.log_notification(relative.id, "email", event_id, "sent" if ok else "failed")
            if ok:
                used.append("email")
        return used
