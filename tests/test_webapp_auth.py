"""Telegram WebApp initData validation (pure stdlib, zero-dep suite)."""
from tests._bootstrap import unittest
from ph.web.auth import InitDataError, sign_init_data, validate_init_data

TOKEN = "123456:TEST-FAKE-TOKEN"
NOW = 1_750_000_000


def make(auth_date=NOW - 60, user_id=42, **extra):
    fields = {"auth_date": str(auth_date), "query_id": "AAH",
              "user": {"id": user_id, "first_name": "Maria", "language_code": "ru"}}
    fields.update(extra)
    return sign_init_data(fields, TOKEN)


class TestInitData(unittest.TestCase):
    def test_happy_path(self):
        data = validate_init_data(make(), TOKEN, now=NOW)
        self.assertEqual(data["user"]["id"], 42)
        self.assertEqual(data["user"]["language_code"], "ru")

    def test_forged_hash_rejected(self):
        raw = make()
        # flip the last hex char of the hash
        last = raw[-1]
        forged = raw[:-1] + ("0" if last != "0" else "1")
        with self.assertRaises(InitDataError):
            validate_init_data(forged, TOKEN, now=NOW)

    def test_wrong_token_rejected(self):
        with self.assertRaises(InitDataError):
            validate_init_data(make(), "999:OTHER-TOKEN", now=NOW)

    def test_stale_auth_date_rejected(self):
        raw = make(auth_date=NOW - 7200)
        with self.assertRaises(InitDataError):
            validate_init_data(raw, TOKEN, max_age_s=3600, now=NOW)
        # ...but a custom max_age can allow it
        data = validate_init_data(raw, TOKEN, max_age_s=8000, now=NOW)
        self.assertEqual(data["user"]["id"], 42)

    def test_missing_hash_rejected(self):
        with self.assertRaises(InitDataError):
            validate_init_data("auth_date=1&user=%7B%22id%22%3A1%7D", TOKEN, now=NOW)

    def test_empty_rejected(self):
        with self.assertRaises(InitDataError):
            validate_init_data("", TOKEN, now=NOW)
        with self.assertRaises(InitDataError):
            validate_init_data(make(), "", now=NOW)

    def test_extra_params_still_validate(self):
        # signature covers sorted params, whatever Telegram adds in the future
        data = validate_init_data(make(chat_type="private", start_param="x"), TOKEN, now=NOW)
        self.assertEqual(data["chat_type"], "private")
