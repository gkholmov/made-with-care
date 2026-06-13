"""Shared test setup (stdlib unittest, no third-party deps).
Sets env BEFORE importing ph, then exposes a Base TestCase + helpers."""
import os
import sys
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.gettempdir()}/ph_unittest.db")
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("STT_PROVIDER", "stub")
os.environ.setdefault("TTS_PROVIDER", "stub")
os.environ.setdefault("EMAIL_PROVIDER", "stub")

from ph.db import models, store          # noqa: E402
from ph.providers.email import StubEmail  # noqa: E402
from ph.notifications import Notifier      # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        models.reset_db()
        StubEmail.sent.clear()

    def make_elder(self, name="Maria", language="en", tg_id=1001, rel_tg=2002,
                   email="kid@example.com"):
        e = store.get_or_create_elder(tg_id, name, language)
        store.set_profile(e.id, "ios", "old")
        store.link_relative(e.id, "Anna", email, rel_tg, language)
        return e.id, store.get_trusted_relative(e.id)

    def notifier(self):
        sent = []
        n = Notifier(telegram_send=lambda c, t: sent.append((c, t)) or True, email=StubEmail())
        n.sent_tg = sent
        return n
