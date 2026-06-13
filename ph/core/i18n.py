"""Static, exact localization for UI chrome + safety messages (RU / EN / DE).

These strings must NOT be left to the LLM — they are the fixed, trustworthy parts
of the experience (buttons that never move, safety warnings that must be precise).
Dynamic step phrasing/translation is the LLM's job (see ph.providers.llm).
"""
from __future__ import annotations
from ph.config import settings

STR = {
    "btn_problem": {"en": "🎙️ Tell me the problem", "ru": "🎙️ Расскажите, что случилось",
                    "de": "🎙️ Sagen Sie, was los ist"},
    "btn_photo":   {"en": "📷 Show me your screen", "ru": "📷 Покажите экран",
                    "de": "📷 Zeigen Sie den Bildschirm"},
    "btn_call":    {"en": "📞 Call {name}", "ru": "📞 Позвонить {name}",
                    "de": "📞 {name} anrufen"},
    # Topic shortcuts on the home keyboard — one per playbook.
    "btn_t_wifi":      {"en": "📶 Internet", "ru": "📶 Интернет", "de": "📶 Internet"},
    "btn_t_password":  {"en": "🔑 Password", "ru": "🔑 Пароль", "de": "🔑 Passwort"},
    "btn_t_os_update": {"en": "📱 Phone updated", "ru": "📱 Телефон обновился",
                        "de": "📱 Handy aktualisiert"},
    "btn_t_setup":     {"en": "🔍 Make it easier", "ru": "🔍 Сделать крупнее",
                        "de": "🔍 Einfacher machen"},
    "btn_t_scam":      {"en": "⚠️ Suspicious message", "ru": "⚠️ Подозрительное сообщение",
                        "de": "⚠️ Verdächtige Nachricht"},
    # Opens the Telegram Mini App (shown only when WEBAPP_URL is configured).
    "btn_open_app": {"en": "🟢 Open my helper", "ru": "🟢 Открыть помощника",
                     "de": "🟢 Helfer öffnen"},
    # Confirmation buttons shown after a "did it work?" step. The words are chosen so
    # intent.sentiment() still classifies them correctly if a tap arrives as raw text.
    "btn_yes_done": {"en": "✅ It worked", "ru": "✅ Получилось", "de": "✅ Hat geklappt"},
    "btn_not_yet":  {"en": "❌ Not yet",  "ru": "❌ Пока нет",   "de": "❌ Noch nicht"},
    # Exact progress prefix for playbook steps (added in code, never by the LLM).
    "step_progress": {"en": "Step {n} of {total}: ", "ru": "Шаг {n} из {total}: ",
                      "de": "Schritt {n} von {total}: "},
    "greeting": {
        "en": "Hello {name}! I'm your helper. I'm an automatic computer helper, not a person — "
              "and if anything ever looks risky, I let your family know right away. "
              "Tap a big button below, or just talk to me. "
              "I will never ask for your passwords, codes, or money.",
        "ru": "Здравствуйте, {name}! Я ваш помощник. Я — автоматический помощник, компьютерная программа, "
              "а не человек. Если что-то покажется опасным, я сразу сообщу вашим близким. "
              "Нажмите большую кнопку внизу или просто скажите, "
              "что случилось. Я никогда не спрошу пароли, коды или деньги.",
        "de": "Hallo {name}! Ich bin Ihr Helfer. Ich bin ein automatischer Computer-Helfer, kein Mensch. "
              "Wenn etwas riskant aussieht, gebe ich sofort Ihrer Familie Bescheid. "
              "Tippen Sie unten auf eine große Taste oder sprechen Sie "
              "einfach mit mir. Ich frage niemals nach Passwörtern, Codes oder Geld.",
    },
    "ask_problem": {"en": "I'm listening. Tell me what's wrong, or show me your screen.",
                    "ru": "Я слушаю. Скажите, что не так, или покажите экран.",
                    "de": "Ich höre zu. Sagen Sie, was nicht stimmt, oder zeigen Sie den Bildschirm."},
    "ask_photo": {"en": "Good idea. Take a photo of the screen with the problem and send it to me here.",
                  "ru": "Хорошая идея. Сфотографируйте экран, где видна проблема, и отправьте фото сюда.",
                  "de": "Gute Idee. Machen Sie ein Foto vom Bildschirm mit dem Problem und senden Sie es mir hier."},
    "clarify": {"en": "I want to help. Can you say that in a few words — for example "
                      "'my wifi is off' or 'I forgot my password'? Or tap Call {name}.",
                "ru": "Хочу помочь. Скажите в двух словах — например «не работает вай-фай» или "
                      "«забыл пароль»? Или нажмите «Позвонить {name}».",
                "de": "Ich möchte helfen. Sagen Sie es in wenigen Worten — z. B. „WLAN geht nicht“ oder "
                      "„Passwort vergessen“? Oder tippen Sie auf „{name} anrufen“."},
    "resolved": {"en": "Wonderful — I'm glad that worked! I'm here whenever you need me. 🌼",
                 "ru": "Замечательно — рад, что получилось! Я всегда рядом, когда нужно. 🌼",
                 "de": "Wunderbar — schön, dass es geklappt hat! Ich bin da, wann immer Sie mich brauchen. 🌼"},
    "safety_stop": {
        "en": "Please STOP and don't share any codes, passwords, or money. This can be a scam. "
              "I've let {name} know — please wait and talk to them first.",
        "ru": "Пожалуйста, ОСТАНОВИТЕСЬ и не сообщайте коды, пароли и не отправляйте деньги. "
              "Это может быть мошенничество. Я сообщил {name} — подождите и поговорите с ними.",
        "de": "Bitte STOPP — geben Sie keine Codes, Passwörter oder Geld weiter. Das kann Betrug sein. "
              "Ich habe {name} informiert — bitte warten Sie und sprechen Sie zuerst mit ihnen.",
    },
    "escalating": {"en": "Let's get {name} to help. I'm calling them in for you now.",
                   "ru": "Давайте позовём {name}. Я сейчас сообщу им.",
                   "de": "Holen wir {name} dazu. Ich benachrichtige sie jetzt für Sie."},
    "deleted": {"en": "All your data has been deleted. Goodbye for now. 🌼",
                "ru": "Все ваши данные удалены. До встречи. 🌼",
                "de": "Alle Ihre Daten wurden gelöscht. Bis bald. 🌼"},
    # Bot command menu descriptions (registered with Telegram per language).
    "cmd_start":  {"en": "Start / open my helper", "ru": "Начать / открыть помощника",
                   "de": "Starten / Helfer öffnen"},
    "cmd_setup":  {"en": "Set up help for a relative", "ru": "Настроить помощь для близкого",
                   "de": "Hilfe für Angehörige einrichten"},
    "cmd_delete": {"en": "Delete all my data", "ru": "Удалить все мои данные",
                   "de": "Alle meine Daten löschen"},
    "cmd_cancel": {"en": "Cancel setup", "ru": "Отменить настройку",
                   "de": "Einrichtung abbrechen"},
}

# Commands shown in the Telegram "/" menu, in display order.
COMMANDS = ["start", "setup", "delete", "cancel"]


def command_descriptions(lang: str) -> list:
    """(command, localized description) pairs for Telegram's set_my_commands."""
    return [(c, t(f"cmd_{c}", lang)) for c in COMMANDS]

# Notification text sent to the relative (in the relative's language).
RELATIVE_NOTICE = {
    "en": "Your relative {elder} asked for help with: {reason}. The helper paused and asked them "
          "to wait for you. You can call them now.",
    "ru": "Ваш близкий {elder} попросил помощи: {reason}. Помощник остановился и попросил подождать вас. "
          "Вы можете позвонить им сейчас.",
    "de": "Ihr Angehöriger {elder} bat um Hilfe bei: {reason}. Der Helfer hat pausiert und gebeten, auf Sie "
          "zu warten. Sie können jetzt anrufen.",
}


# Free-form answers accepted for the setup language question.
LANG_ALIASES = {
    "en": "en", "eng": "en", "english": "en", "английский": "en", "englisch": "en",
    "ru": "ru", "rus": "ru", "russian": "ru", "русский": "ru", "русски": "ru",
    "по-русски": "ru", "russisch": "ru",
    "de": "de", "ger": "de", "german": "de", "deutsch": "de", "немецкий": "de",
}


def normalize_lang(text: str) -> str:
    """Map a free-form language answer to a supported code, or '' if unrecognized."""
    return LANG_ALIASES.get(text.strip().lower().rstrip(".!,"), "")


_EN_HINTS = {"the", "is", "my", "not", "it", "to", "and", "i", "can", "what", "how",
             "help", "working", "phone", "please"}
_DE_HINTS = {"nicht", "und", "ist", "mein", "meine", "das", "der", "die", "ich",
             "kein", "keine", "funktioniert", "hilfe", "bitte", "handy"}


def detect_lang(text: str) -> str:
    """Best-effort detection of the language the elder writes in, for auto-switching
    their profile. Conservative: returns '' unless reasonably confident, so short
    confirmations like 'ok' / 'yes' never flip the language."""
    import re
    low = text.lower()
    if sum(1 for ch in low if "а" <= ch <= "я" or ch == "ё") >= 2:
        return "ru"
    if any(ch in low for ch in "äöüß"):
        return "de"
    words = re.findall(r"[a-z']+", low)
    if len(words) >= 3:
        de = sum(w in _DE_HINTS for w in words)
        en = sum(w in _EN_HINTS for w in words)
        if de >= 2 and de > en:
            return "de"
        if en >= 2 and en > de:
            return "en"
    return ""


def t(key: str, lang: str, **kw) -> str:
    lang = lang if lang in settings.supported_langs else settings.default_lang
    template = STR.get(key, {}).get(lang) or STR.get(key, {}).get("en", key)
    try:
        return template.format(**kw)
    except (KeyError, IndexError):
        return template
