"""Pure-logic tests (no DB): redaction, safety gate, intent, i18n, keyboard, playbooks."""
from tests._bootstrap import unittest
from ph.core.redaction import redact, contains_secret
from ph.core import safety, intent, playbooks
from ph.core.i18n import t, normalize_lang, detect_lang, command_descriptions
from ph.ui.keyboard import button_labels, match_button, confirm_labels, match_confirm


class TestRedaction(unittest.TestCase):
    def test_otp_and_cards(self):
        self.assertNotIn("123456", redact("my code is 123456"))
        self.assertNotIn("4111 1111 1111 1111", redact("card 4111 1111 1111 1111"))
        self.assertEqual(redact("hello there"), "hello there")

    def test_password_kv_multilingual(self):
        self.assertNotIn("hunter2", redact("my password is hunter2"))
        self.assertNotIn("qwerty", redact("пароль: qwerty"))
        self.assertNotIn("geheim", redact("mein Passwort ist geheim"))

    def test_contains_secret(self):
        self.assertTrue(contains_secret("the otp is 9981"))
        self.assertFalse(contains_secret("the wifi light is green"))


class TestSafety(unittest.TestCase):
    def test_scam_multilingual(self):
        for txt in ["they asked me to buy a gift card", "мошенник просит подарочная карта",
                    "ich soll einen Gutschein kaufen", "install anydesk so I can fix it",
                    "a federal agent called about my arrest"]:
            self.assertEqual(safety.classify(txt), "scam", txt)

    def test_financial(self):
        for txt in ["I forgot my bank account password", "пароль от банка не подходит",
                    "mein Bank-Passwort funktioniert nicht"]:
            self.assertEqual(safety.classify(txt), "financial", txt)

    def test_benign(self):
        for txt in ["my wifi is not working", "the phone updated and looks different",
                    "не работает интернет"]:
            self.assertTrue(safety.is_safe(txt), txt)


class TestIntent(unittest.TestCase):
    def test_routes(self):
        self.assertEqual(intent.route("my wifi is not working"), "wifi")
        self.assertEqual(intent.route("не работает интернет"), "wifi")
        self.assertEqual(intent.route("ich habe mein Passwort vergessen"), "password")
        self.assertEqual(intent.route("the phone updated and looks different"), "os_update")
        self.assertEqual(intent.route("make the text bigger, help me set up"), "setup")
        self.assertEqual(intent.route("is this real or a strange message"), "scam")
        self.assertIsNone(intent.route("the weather is nice today"))

    def test_sentiment(self):
        self.assertEqual(intent.sentiment("yes it worked"), "affirmative")
        self.assertEqual(intent.sentiment("да, получилось"), "affirmative")
        self.assertEqual(intent.sentiment("no it didn't work"), "negative")
        self.assertEqual(intent.sentiment("nein, geht nicht"), "negative")
        self.assertEqual(intent.sentiment("maybe later"), "other")


class TestPlaybooks(unittest.TestCase):
    def test_five_present_and_wellformed(self):
        self.assertEqual(set(playbooks.REGISTRY), {"wifi", "password", "os_update", "setup", "scam"})
        for name, pb in playbooks.REGISTRY.items():
            self.assertTrue(pb.steps, name)
            self.assertIn(pb.on_exhaust, ("escalate", "resolved"))
            for st in pb.steps:
                self.assertTrue(st.instruction.strip())

    def test_wifi_and_scam(self):
        self.assertTrue(all(s.check for s in playbooks.WIFI.steps))
        self.assertEqual(playbooks.WIFI.on_exhaust, "escalate")
        self.assertEqual(playbooks.SCAM.flag_event, "scam_flag")


class TestI18nKeyboard(unittest.TestCase):
    def test_three_buttons(self):
        for lang in ("en", "ru", "de"):
            labels = button_labels(lang, "Anna")
            self.assertEqual(len(labels), 3)
            self.assertTrue(all(labels))
            self.assertIn("Anna", labels[2])

    def test_roundtrip(self):
        labels = button_labels("en", "Anna")
        self.assertEqual(match_button(labels[0], "en", "Anna"), "problem")
        self.assertEqual(match_button(labels[2], "en", "Anna"), "call")
        self.assertIsNone(match_button("random", "en", "Anna"))

    def test_localized_and_fallback(self):
        self.assertNotEqual(t("safety_stop", "en", name="A"), t("safety_stop", "ru", name="A"))
        self.assertIn("scam", t("safety_stop", "en", name="A").lower())
        self.assertEqual(t("resolved", "fr"), t("resolved", "en"))

    def test_normalize_lang_accepts_natural_answers(self):
        for raw, want in (("ru", "ru"), ("Русский", "ru"), ("RUSSIAN", "ru"), ("по-русски", "ru"),
                          ("Deutsch", "de"), ("german", "de"), ("English", "en"), ("en.", "en"),
                          ("french", ""), ("", "")):
            self.assertEqual(normalize_lang(raw), want, raw)

    def test_detect_lang(self):
        self.assertEqual(detect_lang("Я не могу подключиться к Wi-Fi"), "ru")
        self.assertEqual(detect_lang("да"), "ru")
        self.assertEqual(detect_lang("Mein Handy funktioniert nicht"), "de")
        self.assertEqual(detect_lang("my wifi is not working"), "en")
        # Too short / ambiguous: never flips the stored language.
        self.assertEqual(detect_lang("ok"), "")
        self.assertEqual(detect_lang("yes"), "")
        self.assertEqual(detect_lang("123 456"), "")

    def test_ask_photo_localized(self):
        # The photo button must answer with an instruction, not echo the button label.
        for lang in ("en", "ru", "de"):
            self.assertNotEqual(t("ask_photo", lang), t("btn_photo", lang))
        self.assertIn("экран", t("ask_photo", "ru"))

    def test_confirm_buttons(self):
        for lang in ("en", "ru", "de"):
            yes, no = confirm_labels(lang)
            self.assertTrue(yes and no and yes != no, lang)
            self.assertEqual(match_confirm(yes, lang), "yes")
            self.assertEqual(match_confirm(no, lang), "no")
            # Defense in depth: even as raw text the labels classify correctly.
            self.assertEqual(intent.sentiment(yes), "affirmative", yes)
            self.assertEqual(intent.sentiment(no), "negative", no)
        self.assertIsNone(match_confirm("random", "en"))
        self.assertNotEqual(confirm_labels("ru"), confirm_labels("en"))

    def test_step_progress_localized(self):
        seen = set()
        for lang in ("en", "ru", "de"):
            s = t("step_progress", lang, n=2, total=3)
            self.assertIn("2", s)
            self.assertIn("3", s)
            seen.add(s)
        self.assertEqual(len(seen), 3)  # all three languages differ

    def test_greeting_discloses_ai(self):
        marker = {"en": "automatic", "ru": "автомат", "de": "automatisch"}
        for lang in ("en", "ru", "de"):
            g = t("greeting", lang, name="Maria")
            self.assertIn("Maria", g)
            self.assertIn(marker[lang], g.lower(), lang)

    def test_command_descriptions(self):
        for lang in ("en", "ru", "de"):
            pairs = command_descriptions(lang)
            self.assertEqual(len(pairs), 4)
            for name, desc in pairs:
                self.assertRegex(name, r"^[a-z0-9_]{1,32}$")
                self.assertTrue(3 <= len(desc) <= 256, (name, lang))
        self.assertNotEqual(command_descriptions("ru"), command_descriptions("en"))
