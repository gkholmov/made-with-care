"""Mini App HTTP API tests. Venv-only: skipped cleanly when FastAPI isn't
installed, so the zero-dependency suite stays runnable on system Python."""
import time

from tests._bootstrap import Base, unittest
from ph.db import store
from ph.web.auth import sign_init_data

try:
    from fastapi.testclient import TestClient
    HAS_WEB = True
except ImportError:
    HAS_WEB = False

FAKE_TOKEN = "123456:TEST-FAKE-TOKEN"


@unittest.skipUnless(HAS_WEB, "fastapi not installed (venv-only test)")
class TestWebApi(Base):
    @classmethod
    def setUpClass(cls):
        from ph.config import settings
        from ph.web import api as api_module
        cls._settings = settings
        cls._orig_token = settings.telegram_token
        cls._orig_bot = settings.bot_username
        # frozen dataclass: tests may still pin deterministic values
        object.__setattr__(settings, "telegram_token", FAKE_TOKEN)
        object.__setattr__(settings, "bot_username", "testbot")
        cls.client = TestClient(api_module.app)

    @classmethod
    def tearDownClass(cls):
        object.__setattr__(cls._settings, "telegram_token", cls._orig_token)
        object.__setattr__(cls._settings, "bot_username", cls._orig_bot)

    def auth(self, tg_id: int) -> dict:
        raw = sign_init_data({"auth_date": str(int(time.time())),
                              "user": {"id": tg_id, "first_name": "T"}}, FAKE_TOKEN)
        return {"Authorization": f"tma {raw}"}

    def test_unauthenticated_rejected(self):
        self.assertEqual(self.client.get("/api/me").status_code, 401)
        self.assertEqual(
            self.client.get("/api/me", headers={"Authorization": "tma forged=1&hash=ab"}).status_code,
            401)
        # dev scheme is OFF unless WEBAPP_INSECURE_DEV=1
        self.assertEqual(
            self.client.get("/api/me", headers={"Authorization": "dev 1001"}).status_code, 401)

    def test_me_roles(self):
        eid, rel = self.make_elder(tg_id=1001, rel_tg=2002)
        me = self.client.get("/api/me", headers=self.auth(1001)).json()
        self.assertEqual((me["role"], me["elder_id"]), ("elder", eid))
        me = self.client.get("/api/me", headers=self.auth(2002)).json()
        self.assertEqual(me["role"], "relative")
        me = self.client.get("/api/me", headers=self.auth(7777)).json()
        self.assertEqual(me["role"], "unknown")

    def test_elder_home_labels_match_chat_keyboard(self):
        self.make_elder(language="ru", tg_id=1001)
        home = self.client.get("/api/elder/home", headers=self.auth(1001)).json()
        from ph.ui.keyboard import topic_labels
        self.assertEqual([t["label"] for t in home["topics"]], topic_labels("ru"))

    def test_relative_sees_only_linked_elders(self):
        eid, rel = self.make_elder(tg_id=1001, rel_tg=2002)
        other_eid, _ = self.make_elder(name="Boris", tg_id=1003, rel_tg=3003)
        rows = self.client.get("/api/relative/elders", headers=self.auth(2002)).json()
        self.assertEqual([r["elder_id"] for r in rows], [eid])
        # non-owned elder is a 404, not a 403 (ids must not be enumerable)
        r = self.client.get(f"/api/relative/elders/{other_eid}", headers=self.auth(2002))
        self.assertEqual(r.status_code, 404)
        ok = self.client.get(f"/api/relative/elders/{eid}", headers=self.auth(2002))
        self.assertEqual(ok.status_code, 200)

    def test_sessions_have_no_turn_text(self):
        eid, rel = self.make_elder(tg_id=1001, rel_tg=2002)
        from ph.core import orchestrator
        orchestrator.handle(eid, "Maria", "en", "my wifi is not working", notifier=self.notifier())
        rows = self.client.get(f"/api/relative/elders/{eid}/sessions",
                               headers=self.auth(2002)).json()
        self.assertEqual(rows[0]["scenario"], "wifi")
        self.assertEqual(set(rows[0]),
                         {"scenario", "step", "state", "resolved", "escalated", "started_at"})

    def test_setup_wizard_creates_join_link(self):
        res = self.client.post("/api/relative/setup", headers=self.auth(5005), json={
            "name": "Ira", "language": "ru", "phone_os": "android", "phone_age": "old",
            "email": "kid@example.com", "relative_name": "Anna"})
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertIn("join_", body["link"])
        # the new relative is now known and sees the pending elder
        rows = self.client.get("/api/relative/elders", headers=self.auth(5005)).json()
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["claimed"])
        detail = self.client.get(f"/api/relative/elders/{rows[0]['elder_id']}",
                                 headers=self.auth(5005)).json()
        self.assertEqual(detail["join_link"], body["link"])

    def test_elder_topic_returns_reply_in_app(self):
        from ph.db import store
        eid, rel = self.make_elder(tg_id=1001, rel_tg=2002)
        r = self.client.post("/api/elder/topic", headers=self.auth(1001), json={"name": "wifi"})
        self.assertEqual(r.status_code, 200)
        reply = r.json()["reply"]
        self.assertIn("fan", reply["text"].lower())          # guidance-grounded reply, in-app
        self.assertEqual(reply["state"], "active")
        self.assertEqual(store.active_session(eid).scenario, "wifi")
        bad = self.client.post("/api/elder/topic", headers=self.auth(1001), json={"name": "nope"})
        self.assertEqual(bad.status_code, 400)
        forbidden = self.client.post("/api/elder/topic", headers=self.auth(2002), json={"name": "wifi"})
        self.assertEqual(forbidden.status_code, 404)         # relative can't drive elder actions

    def test_elder_message_yes_resolves(self):
        from ph.db import store
        eid, rel = self.make_elder(tg_id=1001)
        self.client.post("/api/elder/topic", headers=self.auth(1001), json={"name": "wifi"})
        r = self.client.post("/api/elder/message", headers=self.auth(1001), json={"text": "yes"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["reply"]["state"], "resolved")
        self.assertIn("resolved", store.events(eid))

    def test_elder_photo_with_image(self):
        from ph.db import store
        eid, rel = self.make_elder(tg_id=1001)
        r = self.client.post("/api/elder/photo", headers=self.auth(1001),
                             json={"image_b64": "aGVsbG8=", "mime": "image/jpeg"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("reply", r.json())
        # a 'photo' turn was recorded; the raw image is not persisted
        turns = store.conversation_turns(eid)
        self.assertTrue(any(m == "photo" for (_d, m, _t) in turns))
        self.assertNotIn("aGVsbG8", store.all_turn_text())

    def test_elder_voice_transcribes_and_drives(self):
        import base64
        from ph.db import store
        eid, rel = self.make_elder(tg_id=1001)  # StubSTT → "My wifi is not working"
        clip = base64.b64encode(b"fake-audio-bytes").decode()
        r = self.client.post("/api/elder/voice", headers=self.auth(1001),
                             json={"audio_b64": clip, "mime": "audio/webm"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["transcript"], "My wifi is not working")
        self.assertEqual(body["reply"]["state"], "active")
        self.assertEqual(store.active_session(eid).scenario, "wifi")
        bad = self.client.post("/api/elder/voice", headers=self.auth(1001),
                               json={"audio_b64": "!!not-base64!!", "mime": "audio/webm"})
        self.assertEqual(bad.status_code, 400)

    def test_elder_conversation_history_and_empty(self):
        eid, rel = self.make_elder(tg_id=1001)
        empty = self.client.get("/api/elder/conversation", headers=self.auth(1001)).json()
        self.assertEqual(empty, {"active": False, "turns": []})
        self.client.post("/api/elder/topic", headers=self.auth(1001), json={"name": "wifi"})
        conv = self.client.get("/api/elder/conversation", headers=self.auth(1001)).json()
        self.assertTrue(conv["active"])
        self.assertEqual(conv["turns"][0]["role"], "me")     # the trigger (inbound) first
        self.assertEqual(conv["turns"][-1]["role"], "bot")   # the reply (outbound) last
        self.assertIn("fan", conv["turns"][-1]["text"].lower())

    def test_patch_settings(self):
        eid, rel = self.make_elder(tg_id=1001, rel_tg=2002)
        r = self.client.patch(f"/api/relative/elders/{eid}", headers=self.auth(2002),
                              json={"language": "de", "phone_os": "android"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(store.get_elder(eid).language, "de")
        self.assertEqual(store.get_profile(eid)["phone_os"], "android")
        self.assertIn("settings_changed", store.events(eid))
        bad = self.client.patch(f"/api/relative/elders/{eid}", headers=self.auth(2002),
                                json={"language": "xx"})
        self.assertEqual(bad.status_code, 422)
