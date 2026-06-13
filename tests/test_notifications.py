"""Escalation fan-out to Telegram + email."""
from tests._bootstrap import Base, store
from ph.notifications import Notifier
from ph.providers.email import StubEmail


class TestNotifications(Base):
    def test_both_channels(self):
        eid, rel = self.make_elder()
        sent = []
        n = Notifier(telegram_send=lambda c, t: sent.append((c, t)) or True, email=StubEmail())
        ev = store.log_event(eid, "escalation", "wifi")
        used = n.escalate("Maria", "wifi", rel, ev.id)
        self.assertEqual(set(used), {"telegram", "email"})
        self.assertEqual(sent[0][0], rel.telegram_id)
        self.assertEqual(StubEmail.sent[0]["to"], rel.email)
        self.assertEqual(store.notification_channels(), {"telegram", "email"})

    def test_email_only_when_no_telegram(self):
        eid, rel = self.make_elder(rel_tg=None)
        rel = store.get_trusted_relative(eid)
        n = Notifier(telegram_send=lambda c, t: True, email=StubEmail())
        self.assertEqual(n.escalate("Maria", "wifi", rel, None), ["email"])

    def test_no_relative_no_crash(self):
        n = Notifier(telegram_send=lambda c, t: True, email=StubEmail())
        self.assertEqual(n.escalate("Maria", "wifi", None, None), [])
