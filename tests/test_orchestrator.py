"""End-to-end conversation flows through the orchestrator (stub LLM, sqlite)."""
from tests._bootstrap import Base
from ph.core import orchestrator
from ph.db import store
from ph.providers.email import StubEmail


class TestFlows(Base):
    def test_wifi_resolved(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r1 = orchestrator.handle(eid, "Maria", "en", "my wifi is not working", notifier=n)
        self.assertEqual(r1.state, "active")
        self.assertIn("fan", r1.text.lower())
        r2 = orchestrator.handle(eid, "Maria", "en", "yes it works now", notifier=n)
        self.assertEqual(r2.state, "resolved")
        self.assertIn("resolved", store.events(eid))

    def test_wifi_escalates(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        orchestrator.handle(eid, "Maria", "en", "my wifi is not working", notifier=n)
        orchestrator.handle(eid, "Maria", "en", "no", notifier=n)
        orchestrator.handle(eid, "Maria", "en", "no", notifier=n)
        final = orchestrator.handle(eid, "Maria", "en", "no still nothing", notifier=n)
        self.assertEqual(final.state, "escalated")
        self.assertIn("escalation", store.events(eid))
        self.assertEqual(len(n.sent_tg), 1)
        self.assertEqual(len(StubEmail.sent), 1)

    def test_financial_safety_stop(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r = orchestrator.handle(eid, "Maria", "en", "I forgot my bank account password", notifier=n)
        self.assertEqual(r.state, "safety_stop")
        self.assertIn("safety_stop", store.events(eid))
        self.assertEqual(len(n.sent_tg), 1)
        self.assertEqual(len(StubEmail.sent), 1)

    def test_scam_question_escalates(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r1 = orchestrator.handle(eid, "Maria", "en", "is this real? a strange message", notifier=n)
        self.assertEqual(r1.state, "active")
        self.assertIn("scam_flag", store.events(eid))
        orchestrator.handle(eid, "Maria", "en", "ok", notifier=n)
        r3 = orchestrator.handle(eid, "Maria", "en", "ok", notifier=n)
        self.assertEqual(r3.state, "escalated")

    def test_os_update_resolves(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        orchestrator.handle(eid, "Maria", "en", "the phone updated and looks different", notifier=n)
        orchestrator.handle(eid, "Maria", "en", "my phone app is gone", notifier=n)
        r = orchestrator.handle(eid, "Maria", "en", "yes found it", notifier=n)
        self.assertEqual(r.state, "resolved")

    def test_clarify_unknown(self):
        eid, rel = self.make_elder()
        r = orchestrator.handle(eid, "Maria", "en", "the weather is lovely", notifier=self.notifier())
        self.assertEqual(r.state, "clarify")

    def test_inbound_secret_redacted(self):
        eid, rel = self.make_elder()
        orchestrator.handle(eid, "Maria", "en", "my wifi code is 445566", notifier=self.notifier())
        self.assertNotIn("445566", store.all_turn_text())

    def test_step_progress_prefix(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r1 = orchestrator.handle(eid, "Maria", "en", "my wifi is not working", notifier=n)
        self.assertTrue(r1.text.startswith("Step 1 of 3:"), r1.text)
        r2 = orchestrator.handle(eid, "Maria", "en", "no", notifier=n)
        self.assertTrue(r2.text.startswith("Step 2 of 3:"), r2.text)
        r3 = orchestrator.handle(eid, "Maria", "en", "yes it works now", notifier=n)
        self.assertEqual(r3.state, "resolved")
        self.assertNotIn("Step", r3.text)  # closing/clarify/safety messages stay unprefixed

    def test_clarify_has_no_step_prefix_or_confirm(self):
        eid, rel = self.make_elder()
        r = orchestrator.handle(eid, "Maria", "en", "the weather is lovely", notifier=self.notifier())
        self.assertNotIn("Step", r.text)
        self.assertFalse(r.expect_confirm)
        self.assertFalse(orchestrator.expecting_confirmation(eid))

    def test_expect_confirm_flag(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r1 = orchestrator.handle(eid, "Maria", "en", "my wifi is not working", notifier=n)
        self.assertTrue(r1.expect_confirm)          # wifi step 1 asks yes/no
        self.assertTrue(orchestrator.expecting_confirmation(eid))
        r2 = orchestrator.handle(eid, "Maria", "en", "yes", notifier=n)  # tap sends canonical 'yes'
        self.assertEqual(r2.state, "resolved")
        self.assertFalse(r2.expect_confirm)
        self.assertFalse(orchestrator.expecting_confirmation(eid))

    def test_expect_confirm_false_on_open_question(self):
        eid, rel = self.make_elder()
        n = self.notifier()
        r1 = orchestrator.handle(eid, "Maria", "en", "I forgot my password", notifier=n)
        self.assertEqual(r1.state, "active")
        self.assertFalse(r1.expect_confirm)         # password step 1 is an open question
        self.assertFalse(orchestrator.expecting_confirmation(eid))
