"""Telegram WebApp initData validation (https://core.telegram.org/bots/webapps).

Pure stdlib (hmac/hashlib/urllib/json/time) — no FastAPI import — so it is
covered by the zero-dependency unittest suite like the rest of the core.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import time
from typing import Optional
from urllib.parse import parse_qsl


class InitDataError(ValueError):
    """Raised when initData is missing, forged, malformed, or stale."""


def validate_init_data(init_data: str, bot_token: str,
                       max_age_s: int = 3600, now: Optional[float] = None) -> dict:
    """Verify Telegram's HMAC over initData and return the parsed fields.

    The 'user' field (when present) is returned as a dict. Raises InitDataError
    on any problem; never returns partially-validated data.
    """
    if not init_data or not bot_token:
        raise InitDataError("missing initData or token")
    fields = dict(parse_qsl(init_data, keep_blank_values=True))
    received = fields.pop("hash", None)
    if not received:
        raise InitDataError("missing hash")
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        raise InitDataError("bad hash")
    try:
        auth_date = int(fields.get("auth_date", "0"))
    except ValueError:
        raise InitDataError("bad auth_date")
    current = now if now is not None else time.time()
    if auth_date <= 0 or (current - auth_date) > max_age_s:
        raise InitDataError("stale auth_date")
    if "user" in fields:
        try:
            fields["user"] = json.loads(fields["user"])
        except json.JSONDecodeError:
            raise InitDataError("bad user payload")
        if not isinstance(fields["user"], dict) or "id" not in fields["user"]:
            raise InitDataError("bad user payload")
    return fields


def sign_init_data(fields: dict, bot_token: str) -> str:
    """Build a validly-signed initData query string. Test helper (and a precise
    executable spec of the algorithm) — the bot never needs to sign initData."""
    from urllib.parse import urlencode
    flat = {k: (json.dumps(v, separators=(",", ":")) if isinstance(v, dict) else str(v))
            for k, v in fields.items()}
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(flat.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    flat["hash"] = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(flat)
