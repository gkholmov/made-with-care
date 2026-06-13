"""Store functions backing the Mini App relative dashboard (sqlite, zero-dep)."""
from tests._bootstrap import Base
from ph.db import store


class TestDashboardStore(Base):
    def test_relative_sees_only_linked_elders(self):
        eid, rel = self.make_elder(tg_id=1001, rel_tg=2002)
        # a second, UNRELATED elder+relative
        other_eid, _ = self.make_elder(name="Boris", tg_id=1003, rel_tg=3003)
        elders = store.elders_for_relative(2002)
        self.assertEqual([e.id for e in elders], [eid])         # never the other elder
        self.assertTrue(store.relative_owns_elder(2002, eid))
        self.assertFalse(store.relative_owns_elder(2002, other_eid))
        self.assertFalse(store.relative_owns_elder(9999, eid))  # stranger owns nothing

    def test_find_relatives_by_tg(self):
        self.make_elder(rel_tg=2002)
        self.assertTrue(store.find_relatives_by_tg(2002))
        self.assertEqual(store.find_relatives_by_tg(4444), [])

    def test_recent_sessions_and_events_order_and_limit(self):
        eid, rel = self.make_elder()
        s1 = store.start_session(eid, "wifi")
        store.update_session(s1.id, state="resolved")
        s2 = store.start_session(eid, "scam")
        store.log_event(eid, "resolved", "wifi")
        store.log_event(eid, "scam_flag", "scam")
        sessions = store.recent_sessions(eid)
        self.assertEqual([s.scenario for s in sessions], ["scam", "wifi"])  # newest first
        self.assertEqual(sessions[1].state, "resolved")
        events = store.recent_events(eid, limit=1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, "scam_flag")
        self.assertIsNotNone(store.last_event_at(eid))
        self.assertIsNone(store.last_event_at(999))

    def test_pending_join_token_roundtrip(self):
        token = store.create_pending_elder("Ira", "ru", "android", "old",
                                           "Anna", "kid@example.com", 2002)
        elders = store.elders_for_relative(2002)
        self.assertEqual(len(elders), 1)
        pending = elders[0]
        self.assertIsNone(pending.telegram_id)                  # not claimed yet
        self.assertEqual(store.pending_join_token(pending.id), token)
        store.claim_elder(token, 1010)
        self.assertIsNone(store.pending_join_token(pending.id))  # consumed on claim
        self.assertIsNotNone(store.elders_for_relative(2002)[0].telegram_id)

    def test_notifications_for_relative(self):
        eid, rel = self.make_elder(rel_tg=2002)
        n = self.notifier()
        from ph.core import orchestrator
        orchestrator.handle(eid, "Maria", "en", "I forgot my bank account password", notifier=n)
        notes = store.notifications_for_relative(2002)
        self.assertTrue(notes)
        self.assertEqual(notes[0].event_type, "safety_stop")
        self.assertEqual(store.notifications_for_relative(4444), [])

    def test_get_elder(self):
        eid, rel = self.make_elder()
        self.assertEqual(store.get_elder(eid).id, eid)
        self.assertIsNone(store.get_elder(999))
