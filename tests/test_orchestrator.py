"""Conversational brain flows (stub LLM, sqlite). The stub resolves on an
affirmative message and otherwise echoes the playbook guidance."""
from tests._bootstrap import Base
from ph.core import orchestrator
from ph.db import store
from ph.providers.email import StubEmail


class TestFlows(Base):
    def test_wifi_conversational_resolves(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r1 = orchestrator.handle(eid, "Maria", "en", "my wifi is not working", notifier=n)
        self.assertEqual(r1.state, "active")
        self.assertIn("fan", r1.text.lower())          # guidance-grounded first reply
        r2 = orchestrator.handle(eid, "Maria", "en", "yes it works now", notifier=n)
        self.assertEqual(r2.state, "resolved")
        self.assertIn("resolved", store.events(eid))

    def test_no_auto_escalation(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        orchestrator.handle(eid, "Maria", "en", "my wifi is not working", notifier=n)
        r = None
        for _ in range(5):                              # keeps helping, never gives up at step 3
            r = orchestrator.handle(eid, "Maria", "en", "no still broken", notifier=n)
        self.assertEqual(r.state, "active")
        self.assertNotIn("escalation", store.events(eid))
        self.assertEqual(len(n.sent_tg), 0)

    def test_financial_safety_stop(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r = orchestrator.handle(eid, "Maria", "en", "I forgot my bank account password", notifier=n)
        self.assertEqual(r.state, "safety_stop")
        self.assertIn("safety_stop", store.events(eid))
        self.assertEqual(len(n.sent_tg), 1)
        self.assertEqual(len(StubEmail.sent), 1)

    def test_scam_topic_alerts_family_but_keeps_helping(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r = orchestrator.handle(eid, "Maria", "en", "is this real? a strange message", notifier=n)
        self.assertIn("scam_flag", store.events(eid))
        self.assertEqual(len(n.sent_tg), 1)            # family alerted once, at the start
        self.assertEqual(r.state, "active")            # conversation continues in the app

    def test_explicit_call_request_escalates(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r = orchestrator.handle(eid, "Maria", "en", "please call my son", notifier=n)
        self.assertEqual(r.state, "escalated")
        self.assertIn("escalation", store.events(eid))
        self.assertEqual(len(n.sent_tg), 1)

    def test_photo_is_read_in_context(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        orchestrator.handle(eid, "Maria", "en", "the phone updated and looks different", notifier=n)
        r = orchestrator.handle(eid, "Maria", "en", "(sent a photo of the screen)",
                                modality="photo", photo_present=True,
                                image_b64="aGVsbG8=", image_mime="image/jpeg", notifier=n)
        self.assertEqual(r.state, "active")
        self.assertIn("photo", r.text.lower())         # stub acknowledges the image

    def test_inbound_secret_redacted(self):
        eid, rel = self.make_elder()
        orchestrator.handle(eid, "Maria", "en", "my wifi code is 445566", notifier=self.notifier())
        self.assertNotIn("445566", store.all_turn_text())
