"""Redact secrets BEFORE any user text is stored or sent to a provider.

Conservative by design: it is better to over-redact (e.g. a router model number)
than to ever persist an OTP, card number, or password. This is the storage-side
enforcement of 'no credentials/OTPs/financial data are ever stored'.
"""
from __future__ import annotations
import re

_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_DIGITS = re.compile(r"\b\d{4,}\b")                      # OTP / account / long numbers
# A secret keyword followed by up to ~3 tokens (handles "password is hunter2",
# "пароль: qwerty", "Passwort ist geheim"). Conservative on purpose.
_SECRET_KV = re.compile(
    r"(?i)\b(?:password|passcode|pin|otp|code|"
    r"пароль|код|пин|"            # ru
    r"passwort|kennwort)\b(?:[:\-=\s]+\S+){0,3}"
)


def redact(text: str) -> str:
    if not text:
        return text
    t = _SECRET_KV.sub("[redacted]", text)
    t = _CARD.sub("[redacted-number]", t)
    t = _DIGITS.sub("[redacted-number]", t)
    return t


def contains_secret(text: str) -> bool:
    return bool(_SECRET_KV.search(text or "") or _CARD.search(text or "") or _DIGITS.search(text or ""))
