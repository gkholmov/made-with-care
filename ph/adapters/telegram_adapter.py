"""Telegram messaging adapter (python-telegram-bot v21).

Thin layer: normalize inbound -> ph.core.orchestrator.handle -> render reply with the
3-button keyboard. Telegram-only; imported only when running the bot (not in tests).
"""
from __future__ import annotations
import logging
import httpx
from telegram import (Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
                      InlineKeyboardButton, BotCommand, WebAppInfo, MenuButtonWebApp)
from telegram.constants import ChatAction
from telegram.ext import (Application, CommandHandler, MessageHandler, ConversationHandler,
                          ContextTypes, filters)

from ph.config import settings
from ph.core import orchestrator
from ph.core.i18n import t, command_descriptions
from ph.ui.keyboard import (match_button, match_topic, match_confirm, keyboard_rows,
                            TOPIC_TRIGGERS)
from ph.providers import get_stt, get_tts, get_email
from ph.notifications import Notifier
from ph.db import store

log = logging.getLogger("ph.telegram")

# ---- sync Telegram sender for escalation notices (decoupled from PTB's event loop) ----
def _make_tg_sender(token: str):
    def send(chat_id: int, text: str) -> bool:
        r = httpx.post(f"https://api.telegram.org/bot{token}/sendMessage",
                       json={"chat_id": chat_id, "text": text}, timeout=15)
        return r.status_code == 200
    return send


def _notifier() -> Notifier:
    return Notifier(telegram_send=_make_tg_sender(settings.telegram_token), email=get_email())


def _keyboard(language: str, relative_name: str = "",
              expect_confirm: bool = False) -> ReplyKeyboardMarkup:
    # When the Mini App is configured, the bot is just its launcher: one big "Open my
    # helper" button (+ a Call button for emergencies). All the help happens in the app.
    if settings.webapp_url:
        name = relative_name or {"en": "family", "ru": "родным", "de": "Familie"}.get(language, "family")
        rows = [[KeyboardButton(t("btn_open_app", language),
                                web_app=WebAppInfo(url=settings.webapp_url))],
                [KeyboardButton(t("btn_call", language, name=name))]]
        return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True,
                                   one_time_keyboard=False)
    # No Mini App configured -> full in-chat keyboard (layout from ph.ui.keyboard).
    rows = []
    for spec_row in keyboard_rows(language, relative_name, expect_confirm=expect_confirm,
                                  webapp_url=""):
        row = []
        for btn in spec_row:
            if "web_app" in btn:
                row.append(KeyboardButton(btn["text"], web_app=WebAppInfo(url=btn["web_app"]["url"])))
            else:
                row.append(KeyboardButton(btn["text"]))
        rows.append(row)
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True,
                               one_time_keyboard=False)


def _elder_ctx(tg_id: int):
    """Return (elder, relative) for a known elder, or (None, None)."""
    e = store.find_elder_by_tg(tg_id)
    if not e:
        return None, None
    return e, store.get_trusted_relative(e.id)


# ---------------- onboarding (relative) ----------------
ASK_NAME, ASK_LANG, ASK_OS, ASK_AGE, ASK_EMAIL = range(5)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args or []
    # elder joining via deep link: /start join_<token>
    if args and args[0].startswith("join_"):
        token = args[0][5:]
        e = store.claim_elder(token, update.effective_user.id)
        if not e:
            await update.message.reply_text("That setup link wasn't found. Please ask your relative for a new one.")
            return
        rel = store.get_trusted_relative(e.id)
        await update.message.reply_text(
            t("greeting", e.language, name=e.name or ""),
            reply_markup=_keyboard(e.language, rel.name if rel else ""))
        return
    # otherwise: a relative arriving
    await update.message.reply_text(
        "👋 This bot helps an older relative with everyday phone/computer problems.\n\n"
        "If you're setting it up for a parent or grandparent, send /setup.\n"
        "If your relative sent you here to get help, ask them for their personal link.")


# /setup conversation
async def setup_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Let's set up help for your relative. What's their first name?")
    return ASK_NAME

async def setup_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["name"] = update.message.text.strip()[:120]
    await update.message.reply_text("Which language should the helper speak? (en / ru / de)")
    return ASK_LANG

async def setup_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from ph.core.i18n import normalize_lang
    lang = normalize_lang(update.message.text)
    if not lang:
        await update.message.reply_text(
            "Please answer with one of: en / ru / de (English / Русский / Deutsch).")
        return ASK_LANG
    ctx.user_data["lang"] = lang
    await update.message.reply_text("What phone do they have? (iphone / android)")
    return ASK_OS

async def setup_os(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    v = update.message.text.strip().lower()
    ctx.user_data["os"] = "ios" if "ip" in v or "ios" in v else "android"
    await update.message.reply_text("Is it fairly new or quite old? (new / old)")
    return ASK_AGE

async def setup_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    v = update.message.text.strip().lower()
    ctx.user_data["age"] = "new" if "new" in v else "old"
    await update.message.reply_text("Your email for important alerts (e.g. a possible scam)?")
    return ASK_EMAIL

async def setup_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()[:200]
    d = ctx.user_data
    token = store.create_pending_elder(
        name=d["name"], language=d["lang"], phone_os=d["os"], phone_age=d["age"],
        relative_name=update.effective_user.first_name or "Family",
        relative_email=email, relative_tg=update.effective_user.id)
    me = await ctx.bot.get_me()
    link = f"https://t.me/{me.username}?start=join_{token}"
    await update.message.reply_text(
        "✅ All set! Send your relative this personal link (or open it on their phone):\n\n"
        f"{link}\n\nWhen they tap it, the helper introduces itself with three big buttons. "
        "You'll get a Telegram + email alert if anything risky comes up.")
    return ConversationHandler.END

async def setup_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Setup cancelled. Send /setup to start again.")
    return ConversationHandler.END


# ---------------- elder message handlers ----------------
async def _drive(update: Update, text: str, modality: str, photo_present: bool = False,
                 detect_language: bool = True):
    e, rel = _elder_ctx(update.effective_user.id)
    if not e:
        await update.message.reply_text("Please open your personal setup link first, or ask /setup.")
        return None, None
    try:  # the LLM takes a few seconds; without this the bot looks frozen
        await update.effective_chat.send_action(ChatAction.TYPING)
    except Exception:
        pass  # cosmetic only — never block the real reply
    # The elder writes/speaks in a different supported language -> follow them.
    # (Skipped for button taps: their canonical trigger text is always English.)
    from ph.core.i18n import detect_lang
    det = detect_lang(text) if detect_language else ""
    if det and det != e.language and det in settings.supported_langs:
        store.set_language(e.id, det)
        e.language = det
        log.info("elder %s language auto-switched to %s", e.id, det)
    reply = orchestrator.handle(e.id, e.name, e.language, text, modality=modality,
                                photo_present=photo_present, notifier=_notifier())
    kb = _keyboard(e.language, rel.name if rel else "", expect_confirm=reply.expect_confirm)
    await update.message.reply_text(reply.text, reply_markup=kb)
    return reply.text, e.language


async def _launch_nudge(update: Update, e, rel) -> None:
    """In launcher mode the bot doesn't run the playbook in chat — it points the elder
    to the Mini App, where the whole conversation lives."""
    await update.message.reply_text(
        t("open_in_app", e.language),
        reply_markup=_keyboard(e.language, rel.name if rel else ""))


async def on_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if settings.webapp_url:  # bot is just the launcher; voice help happens in the app
        e, rel = _elder_ctx(update.effective_user.id)
        if e:
            await _launch_nudge(update, e, rel)
            return
    try:  # STT adds a few seconds before _drive shows its own indicator
        await update.effective_chat.send_action(ChatAction.TYPING)
    except Exception:
        pass
    f = await ctx.bot.get_file(update.message.voice.file_id)
    audio = bytes(await f.download_as_bytearray())
    text, _lang = get_stt().transcribe(audio, "audio/ogg")
    reply_text, language = await _drive(update, text, "voice")
    # Voice in -> voice out: the elder may find listening easier than reading.
    if reply_text:
        try:
            await update.effective_chat.send_action(ChatAction.RECORD_VOICE)
            speech = get_tts().synthesize(reply_text, language or "en")
            if speech:
                import io
                await update.message.reply_voice(io.BytesIO(speech))
        except Exception:
            log.exception("voice reply failed (text reply was already sent)")


async def on_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if settings.webapp_url:  # bot is just the launcher; the screen photo goes in the app
        e, rel = _elder_ctx(update.effective_user.id)
        if e:
            await _launch_nudge(update, e, rel)
            return
    # Screen photo: in production the image is passed to the vision LLM. MVP flags its presence.
    await _drive(update, "(sent a photo of the screen)", "photo", photo_present=True)


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    e, rel = _elder_ctx(update.effective_user.id)
    text = update.message.text or ""
    # Is it one of the 3 buttons?
    if e:
        # The Call button always works, even in launcher mode (it's an emergency action).
        is_call = any(match_button(text, lng, rel.name if rel else "") == "call"
                      for lng in dict.fromkeys((e.language, *settings.supported_langs)))
        if is_call:
            if rel and rel.telegram_id:
                kb = InlineKeyboardMarkup([[InlineKeyboardButton(
                    f"📞 {rel.name}", url=f"tg://user?id={rel.telegram_id}")]])
                await update.message.reply_text("Tap to open the chat, then press the call button:",
                                                reply_markup=kb)
            else:
                await update.message.reply_text("I'll let your family know to call you.")
                orchestrator.handle(e.id, e.name, e.language, "please call me", notifier=_notifier())
            return
        # Mini App configured -> the bot is just its launcher; send help into the app.
        if settings.webapp_url:
            await _launch_nudge(update, e, rel)
            return
        # ✅/❌ confirm tap -> canonical yes/no for the brain. Matched in any supported
        # language (the on-screen keyboard may show stale-language labels).
        ans = None
        for lng in dict.fromkeys((e.language, *settings.supported_langs)):
            ans = match_confirm(text, lng)
            if ans:
                break
        if ans:
            if orchestrator.expecting_confirmation(e.id):
                await _drive(update, ans, "button", detect_language=False)
            else:  # stale button (after resolve/restart) — never let it advance anything
                await update.message.reply_text(
                    t("ask_problem", e.language),
                    reply_markup=_keyboard(e.language, rel.name if rel else ""))
            return
        # Match the tap in any supported language: after a language switch the elder's
        # on-screen keyboard may still show the previously cached labels.
        act = None
        for lng in dict.fromkeys((e.language, *settings.supported_langs)):
            act = match_button(text, lng, rel.name if rel else "")
            if act:
                break
        confirm_pending = orchestrator.expecting_confirmation(e.id)
        if act == "problem":
            await update.message.reply_text(
                t("ask_problem", e.language),
                reply_markup=_keyboard(e.language, rel.name if rel else "",
                                       expect_confirm=confirm_pending))
            return
        if act == "photo":
            await update.message.reply_text(
                t("ask_photo", e.language),
                reply_markup=_keyboard(e.language, rel.name if rel else "",
                                       expect_confirm=confirm_pending))
            return
        if act == "call":
            if rel and rel.telegram_id:
                kb = InlineKeyboardMarkup([[InlineKeyboardButton(
                    f"📞 {rel.name}", url=f"tg://user?id={rel.telegram_id}")]])
                await update.message.reply_text("Tap to open the chat, then press the call button:",
                                                reply_markup=kb)
            else:
                await update.message.reply_text("I'll let your family know to call you.")
                # also fire an escalation email
                orchestrator.handle(e.id, e.name, e.language, "please call me", notifier=_notifier())
            return
        # Topic shortcut tapped -> close any current scenario and start that playbook.
        topic = None
        for lng in dict.fromkeys((e.language, *settings.supported_langs)):
            topic = match_topic(text, lng)
            if topic:
                break
        if topic:
            sess = store.active_session(e.id)
            if sess:
                store.update_session(sess.id, state="closed")
            await _drive(update, TOPIC_TRIGGERS[topic], "button", detect_language=False)
            return
    await _drive(update, text, "text")


async def on_web_app_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Taps inside the Mini App (sendData) land here and continue in the chat."""
    e, rel = _elder_ctx(update.effective_user.id)
    if not e:
        return
    import json
    try:
        payload = json.loads(update.effective_message.web_app_data.data)
    except (ValueError, AttributeError):
        return
    action = payload.get("action")
    if action == "topic" and payload.get("name") in TOPIC_TRIGGERS:
        sess = store.active_session(e.id)
        if sess:  # same as a chat topic-button tap: start the chosen playbook fresh
            store.update_session(sess.id, state="closed")
        await _drive(update, TOPIC_TRIGGERS[payload["name"]], "button", detect_language=False)
    elif action == "photo":
        await update.effective_message.reply_text(
            t("ask_photo", e.language),
            reply_markup=_keyboard(e.language, rel.name if rel else ""))


async def delete_me(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ok = store.delete_elder_data(update.effective_user.id)
    e, _ = _elder_ctx(update.effective_user.id)
    lang = e.language if e else "en"
    await update.message.reply_text(t("deleted", lang) if ok else "Nothing to delete.")


async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.error("handler error", exc_info=ctx.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Something went wrong on my side. Please try again in a moment.")
    except Exception:  # never let error reporting raise
        pass


async def _post_init(app: Application):
    """Register the '/' command menu, localized per Telegram client language."""
    try:
        await app.bot.set_my_commands(  # fallback for clients in any other language
            [BotCommand(c, d) for c, d in command_descriptions(settings.default_lang)])
        for lc in settings.supported_langs:
            await app.bot.set_my_commands(
                [BotCommand(c, d) for c, d in command_descriptions(lc)], language_code=lc)
        if settings.webapp_url:  # relatives open the Mini App from the menu button
            await app.bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp("App", WebAppInfo(url=settings.webapp_url)))
    except Exception:
        log.exception("set_my_commands failed (menu may be stale; bot still works)")


def build_application() -> Application:
    app = Application.builder().token(settings.telegram_token).post_init(_post_init).build()
    app.add_error_handler(on_error)
    conv = ConversationHandler(
        entry_points=[CommandHandler("setup", setup_start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_name)],
            ASK_LANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_lang)],
            ASK_OS: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_os)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_age)],
            ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_email)],
        },
        fallbacks=[CommandHandler("cancel", setup_cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("delete", delete_me))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, on_web_app_data))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app
