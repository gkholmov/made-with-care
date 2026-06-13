"""The elder's entire UI: three big, fixed buttons. Pure (no Telegram import) so it
is unit-testable. The Telegram adapter turns these labels into a persistent
ReplyKeyboardMarkup."""
from __future__ import annotations
from ph.core.i18n import t


def button_labels(language: str, relative_name: str = "") -> list[str]:
    """Return the 3 button captions in order: problem / photo / call."""
    name = relative_name or {"en": "family", "ru": "родным", "de": "Familie"}.get(language, "family")
    return [
        t("btn_problem", language),
        t("btn_photo", language),
        t("btn_call", language, name=name),
    ]


def match_button(label: str, language: str, relative_name: str = "") -> str | None:
    """Map a tapped button caption back to an action id."""
    labels = button_labels(language, relative_name)
    actions = ["problem", "photo", "call"]
    for cap, act in zip(labels, actions):
        if label.strip() == cap:
            return act
    return None


# ---- topic shortcuts (one per playbook) ----
TOPIC_ORDER = ["wifi", "password", "os_update", "setup", "scam"]

# Canonical English phrases that intent.route() maps to each playbook; sent to the
# brain when the elder taps a topic button (their own words aren't needed).
TOPIC_TRIGGERS = {
    "wifi": "wifi",
    "password": "password reset",
    "os_update": "update looks different",
    "setup": "bigger text",
    "scam": "suspicious message",
}


def topic_labels(language: str) -> list[str]:
    """Topic button captions, in TOPIC_ORDER."""
    return [t(f"btn_t_{name}", language) for name in TOPIC_ORDER]


def match_topic(label: str, language: str) -> str | None:
    """Map a tapped topic caption back to its playbook name."""
    s = label.strip()
    for name in TOPIC_ORDER:
        if s == t(f"btn_t_{name}", language):
            return name
    return None


# ---- confirmation buttons (shown after a "did it work?" step) ----
def confirm_labels(language: str) -> list[str]:
    """The two confirm captions: [it worked, not yet]."""
    return [t("btn_yes_done", language), t("btn_not_yet", language)]


def match_confirm(label: str, language: str) -> str | None:
    """Map a tapped confirm caption to the canonical answer 'yes' / 'no'."""
    s = label.strip()
    yes, no = confirm_labels(language)
    if s == yes:
        return "yes"
    if s == no:
        return "no"
    return None


# ---- shared keyboard layout (one source of truth for chat + web sender) ----
def keyboard_rows(language: str, relative_name: str = "", expect_confirm: bool = False,
                  webapp_url: str = "") -> list:
    """Home-keyboard rows as plain button specs: each button is {"text": str} plus an
    optional {"web_app": {"url": str}}. Pure (no Telegram import) so both the Telegram
    adapter and the web server's raw sendMessage call build the SAME keyboard — this
    dict shape is exactly Telegram's KeyboardButton JSON."""
    labels = button_labels(language, relative_name)
    tl = topic_labels(language)
    rows = [
        [{"text": labels[0]}],                         # 🎙️ tell the problem
        [{"text": labels[1]}],                         # 📷 show the screen
        [{"text": labels[2]}],                         # 📞 call relative
        [{"text": tl[0]}, {"text": tl[1]}],            # 📶 internet | 🔑 password
        [{"text": tl[2]}, {"text": tl[3]}],            # 📱 updated  | 🔍 easier
        [{"text": tl[4]}],                             # ⚠️ suspicious message
    ]
    if webapp_url:
        rows.insert(0, [{"text": t("btn_open_app", language), "web_app": {"url": webapp_url}}])
    if expect_confirm:
        cl = confirm_labels(language)
        rows.insert(0, [{"text": cl[0]}, {"text": cl[1]}])
    return rows
