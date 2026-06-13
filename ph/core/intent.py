"""Lightweight, deterministic intent routing + reply-sentiment detection (RU/EN/DE).

Keyword routing is reliable and fully testable. A real LLM classifier can be added
later behind the same `route()` function without changing callers.
"""
from __future__ import annotations

_INTENTS = {
    "wifi": ["wifi", "wi-fi", "internet", "online", "network", "router", "no connection", "little fan",
             "вай-фай", "вайфай", "интернет", "сеть", "роутер", "нет связи", "не подключается",
             "wlan", "internetverbindung", "netzwerk", "router", "keine verbindung"],
    "password": ["password", "passcode", "locked out", "can't log in", "cant log in", "sign in", "forgot my",
                 "apple id", "google account", "reset",
                 "пароль", "не могу войти", "заблокирован", "вход", "забыл пароль", "сбросить",
                 "passwort", "kennwort", "anmelden", "gesperrt", "passwort vergessen", "zurücksetzen"],
    "os_update": ["update", "updated", "looks different", "changed", "disappeared", "can't find", "moved",
                  "new version", "different now",
                  "обновил", "обновление", "по-другому", "выглядит иначе", "пропал", "не могу найти", "изменилось",
                  "aktualisiert", "update", "sieht anders", "verschwunden", "finde nicht", "verändert"],
    "setup": ["set up", "setup", "too small", "bigger text", "font", "how do i", "teach me", "use my phone",
              "настроить", "мелкий шрифт", "крупнее", "как мне", "научи", "пользоваться телефоном",
              "einrichten", "zu klein", "größere schrift", "wie kann ich", "zeig mir", "handy benutzen"],
    "scam": ["scam", "is this real", "suspicious", "fraud", "they want", "won a prize", "lottery", "strange message",
             "мошенник", "это правда", "подозрительн", "обман", "выиграл", "странное сообщение",
             "betrug", "ist das echt", "verdächtig", "gewonnen", "seltsame nachricht"],
}

_AFFIRM = ["yes", "yeah", "yep", "done", "worked", "works", "fixed", "connected", "ok", "okay", "got it",
           "да", "ага", "получилось", "работает", "готово", "подключилось", "ок", "хорошо",
           "ja", "hat geklappt", "funktioniert", "fertig", "erledigt", "ok", "geschafft"]
_NEG = ["no", "not", "doesn't", "didn't", "still", "nothing", "can't", "cannot", "nope",
        "нет", "не работает", "не получилось", "всё ещё", "все еще", "ничего", "не могу",
        "nein", "geht nicht", "klappt nicht", "immer noch", "noch nicht", "nichts", "kann nicht"]


def route(text: str) -> str | None:
    low = (text or "").lower()
    best, score = None, 0
    for name, kws in _INTENTS.items():
        hits = sum(1 for k in kws if k in low)
        if hits > score:
            best, score = name, hits
    return best


import re as _re


def _matches(low: str, kws) -> bool:
    """Word-boundary aware: single words match as whole words (so 'no' doesn't fire
    inside 'now'/'know'); multi-word phrases match as substrings."""
    for kw in kws:
        if " " in kw:
            if kw in low:
                return True
        elif _re.search(r"\b" + _re.escape(kw) + r"\b", low):
            return True
    return False


def sentiment(text: str) -> str:
    low = (text or "").lower()
    if _matches(low, _NEG):
        return "negative"   # negatives win (e.g. "no, didn't work")
    if _matches(low, _AFFIRM):
        return "affirmative"
    return "other"
