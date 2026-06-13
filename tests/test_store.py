"""Store: re-onboarding the same Telegram account must merge, not crash."""
from tests._bootstrap import Base, store


class TestReclaim(Base):
    def test_reclaim_same_telegram_account_merges(self):
        eid, _rel = self.make_elder(name="German", language="en", tg_id=1001)
        token = store.create_pending_elder("Ирина", "ru", "ios", "old",
                                           "Anna", "anna@example.com", 2002)
        e = store.claim_elder(token, 1001)  # same account taps the new link
        self.assertIsNotNone(e)
        self.assertEqual(e.id, eid)            # merged into the existing row
        self.assertEqual(e.language, "ru")     # fresh setup wins
        self.assertEqual(e.name, "Ирина")
        rel = store.get_trusted_relative(eid)  # newest relative link wins
        self.assertEqual(rel.name, "Anna")
        self.assertEqual(rel.telegram_id, 2002)

    def test_fresh_claim_still_works(self):
        token = store.create_pending_elder("Maria", "de", "android", "new",
                                           "Hans", "hans@example.com", 3003)
        e = store.claim_elder(token, 5005)
        self.assertEqual(e.language, "de")
        self.assertEqual(store.find_elder_by_tg(5005).id, e.id)
