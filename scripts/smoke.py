"""Offline end-to-end smoke test: simulates an elder conversation without Telegram.
Run: PYTHONPATH=. python3 scripts/smoke.py"""
import os, tempfile
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/ph_smoke.db")
for k in ("LLM_PROVIDER", "STT_PROVIDER", "EMAIL_PROVIDER"):
    os.environ.setdefault(k, "stub")

from ph.db import models, store
from ph.core import orchestrator
from ph.notifications import Notifier
from ph.providers.email import StubEmail

models.reset_db()
sent = []
notifier = Notifier(telegram_send=lambda c, t: sent.append((c, t)) or True, email=StubEmail())

e = store.get_or_create_elder(555, "Maria", "en")
store.set_profile(e.id, "ios", "old")
store.link_relative(e.id, "Anna", "anna@example.com", 999, "en")


def say(text):
    r = orchestrator.handle(e.id, "Maria", "en", text, notifier=notifier)
    print(f"\n👵 Maria: {text}\n🤖 Helper [{r.state}]: {r.text}")
    return r


print("=== Scenario: WiFi (resolved) ===")
say("my wifi is not working")
say("no, still nothing")
say("ok the box lights are steady now")
say("yes it connected!")

print("\n=== Scenario: scam attempt (safety stop + escalation) ===")
say("a man says I must buy a gift card to fix my computer")
print(f"\n🔔 Relative Telegram alerts: {len(sent)} | emails: {len(StubEmail.sent)}")
