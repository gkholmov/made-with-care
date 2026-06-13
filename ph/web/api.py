"""FastAPI app for the Telegram Mini App: JSON API + static SPA.

Imported only by ph.web.main (and venv-only tests) — never by the bot or the
zero-dependency test suite, mirroring how the Telegram adapter is isolated.

Roles (decided server-side from validated initData):
  elder    -> big-button home face
  relative -> dashboard face (sees ONLY elders linked via the `link` table)
  unknown  -> may check /api/me and run the setup wizard (that's how a new
              relative becomes known, mirroring /setup in chat)
"""
from __future__ import annotations
import logging
import pathlib
from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ph.config import settings
from ph.core import orchestrator
from ph.core.i18n import t
from ph.db import store
from ph.notifications import Notifier
from ph.providers import get_email
from ph.ui.keyboard import TOPIC_ORDER, TOPIC_TRIGGERS
from ph.web.auth import InitDataError, validate_init_data

log = logging.getLogger("ph.web")
app = FastAPI(title="Parent Helper Mini App", docs_url=None, redoc_url=None)


def _tg_send(chat_id: int, text: str) -> bool:
    r = httpx.post(f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage",
                   json={"chat_id": chat_id, "text": text}, timeout=15)
    return r.status_code == 200


def _web_notifier() -> Notifier:
    return Notifier(telegram_send=_tg_send, email=get_email())


def _reply_json(r: orchestrator.Reply) -> dict:
    """Serialize an orchestrator Reply for the in-app conversation."""
    return {"reply": {"text": r.text, "state": r.state,
                      "expect_confirm": r.expect_confirm, "show_call": r.show_call}}

_bot_username_cache: dict = {}


def _bot_username() -> str:
    if settings.bot_username:
        return settings.bot_username
    if "name" not in _bot_username_cache:
        try:
            r = httpx.get(f"https://api.telegram.org/bot{settings.telegram_token}/getMe", timeout=10)
            _bot_username_cache["name"] = r.json()["result"]["username"]
        except Exception:
            log.exception("getMe failed; set TELEGRAM_BOT_USERNAME to avoid this lookup")
            return ""
    return _bot_username_cache["name"]


# ---------------- auth ----------------
@dataclass
class Identity:
    role: str                      # elder | relative | unknown
    tg_id: int
    elder: Optional[object] = None


def current_identity(authorization: str = Header("")) -> Identity:
    scheme, _, raw = authorization.partition(" ")
    scheme = scheme.lower()
    if scheme == "dev" and settings.webapp_insecure_dev:
        tg_id = int(raw.strip() or "0")
    elif scheme == "tma":
        try:
            data = validate_init_data(raw, settings.telegram_token,
                                      max_age_s=settings.webapp_auth_max_age)
            tg_id = int(data["user"]["id"])
        except (InitDataError, KeyError, TypeError, ValueError):
            raise HTTPException(status_code=401, detail="invalid initData")
    else:
        raise HTTPException(status_code=401, detail="missing credentials")
    elder = store.find_elder_by_tg(tg_id)
    if elder:
        return Identity(role="elder", tg_id=tg_id, elder=elder)
    if store.find_relatives_by_tg(tg_id):
        return Identity(role="relative", tg_id=tg_id)
    return Identity(role="unknown", tg_id=tg_id)


def _owned_elder(ident: Identity, elder_id: int):
    """404 (not 403) on any mismatch so elder ids are not enumerable."""
    if ident.role != "relative" or not store.relative_owns_elder(ident.tg_id, elder_id):
        raise HTTPException(status_code=404)
    e = store.get_elder(elder_id)
    if not e:
        raise HTTPException(status_code=404)
    return e


# ---------------- shared ----------------
@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/me")
def me(ident: Identity = Depends(current_identity)):
    if ident.role == "elder":
        rel = store.get_trusted_relative(ident.elder.id)
        return {"role": "elder", "tg_id": ident.tg_id, "elder_id": ident.elder.id,
                "name": ident.elder.name, "language": ident.elder.language,
                "relative_name": rel.name if rel else "",
                "bot_username": _bot_username()}
    rels = store.find_relatives_by_tg(ident.tg_id)
    lang = rels[0].language if rels else settings.default_lang
    name = rels[0].name if rels else ""
    return {"role": ident.role, "tg_id": ident.tg_id, "name": name, "language": lang,
            "bot_username": _bot_username()}


# ---------------- elder face ----------------
@app.get("/api/elder/home")
def elder_home(ident: Identity = Depends(current_identity)):
    if ident.role != "elder":
        raise HTTPException(status_code=404)
    e = ident.elder
    rel = store.get_trusted_relative(e.id)
    # Labels come from the same i18n source as the chat keyboard, so the two
    # surfaces can never drift apart.
    return {
        "name": e.name, "language": e.language,
        "relative": {"name": rel.name if rel else "",
                     "telegram_id": rel.telegram_id if rel else None},
        "topics": [{"key": name, "label": t(f"btn_t_{name}", e.language)} for name in TOPIC_ORDER],
        "strings": {
            "greeting_short": t("ask_problem", e.language),
            "photo": t("btn_photo", e.language),
            "call": t("btn_call", e.language, name=(rel.name if rel else "")).strip(),
        },
    }


def _elder(ident: Identity):
    if ident.role != "elder":
        raise HTTPException(status_code=404)
    return ident.elder


class TopicBody(BaseModel):
    name: str


class MessageBody(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@app.post("/api/elder/topic")
def elder_topic(body: TopicBody, ident: Identity = Depends(current_identity)):
    """Start a playbook from an in-app topic tap; the conversation stays in the app."""
    e = _elder(ident)
    if body.name not in TOPIC_TRIGGERS:
        raise HTTPException(status_code=400, detail="unknown topic")
    sess = store.active_session(e.id)
    if sess:  # same as a chat topic-button tap: start the chosen playbook fresh
        store.update_session(sess.id, state="closed")
    reply = orchestrator.handle(e.id, e.name, e.language, TOPIC_TRIGGERS[body.name],
                                modality="button", notifier=_web_notifier())
    return _reply_json(reply)


@app.post("/api/elder/message")
def elder_message(body: MessageBody, ident: Identity = Depends(current_identity)):
    """An in-app answer: a free-typed reply, or the canonical 'yes'/'no' the ✅/❌
    buttons send (intent.sentiment classifies those regardless of the elder's language)."""
    e = _elder(ident)
    reply = orchestrator.handle(e.id, e.name, e.language, body.text,
                                modality="text", notifier=_web_notifier())
    return _reply_json(reply)


@app.post("/api/elder/photo")
def elder_photo(ident: Identity = Depends(current_identity)):
    """The elder showed their screen. v1 only flags presence (no vision yet), so the
    image is never uploaded or stored — strictly more private."""
    e = _elder(ident)
    reply = orchestrator.handle(e.id, e.name, e.language, "(sent a photo of the screen)",
                                modality="photo", photo_present=True, notifier=_web_notifier())
    return _reply_json(reply)


@app.get("/api/elder/conversation")
def elder_conversation(ident: Identity = Depends(current_identity)):
    """Current in-app conversation, so the app can resume where the elder left off."""
    e = _elder(ident)
    sess = store.active_session(e.id)
    if not sess:
        return {"active": False, "turns": []}
    turns = [{"role": "bot" if d == "out" else "me", "text": text, "modality": m}
             for (d, m, text) in store.conversation_turns(e.id)]
    return {"active": True, "state": sess.state,
            "expect_confirm": orchestrator.expecting_confirmation(e.id), "turns": turns}


# ---------------- relative dashboard ----------------
@app.get("/api/relative/elders")
def relative_elders(ident: Identity = Depends(current_identity)):
    if ident.role != "relative":
        raise HTTPException(status_code=404)
    out = []
    for e in store.elders_for_relative(ident.tg_id):
        evs = store.recent_events(e.id, limit=10)
        out.append({
            "elder_id": e.id, "name": e.name, "language": e.language,
            "claimed": e.telegram_id is not None,
            "last_event_at": store.last_event_at(e.id),
            "open_alerts": sum(1 for ev in evs if ev.type in ("safety_stop", "escalation", "scam_flag")),
        })
    return out


@app.get("/api/relative/elders/{elder_id}")
def relative_elder_detail(elder_id: int, ident: Identity = Depends(current_identity)):
    e = _owned_elder(ident, elder_id)
    profile = store.get_profile(elder_id)
    token = store.pending_join_token(elder_id)
    bot = _bot_username()
    return {
        "elder_id": elder_id, "name": e.name, "language": e.language,
        "claimed": e.telegram_id is not None,
        "consent_at": e.consent_at,
        "phone_os": profile["phone_os"], "phone_age": profile["phone_age"],
        "join_link": f"https://t.me/{bot}?start=join_{token}" if (token and bot) else None,
    }


@app.get("/api/relative/elders/{elder_id}/sessions")
def relative_elder_sessions(elder_id: int, limit: int = 20,
                            ident: Identity = Depends(current_identity)):
    _owned_elder(ident, elder_id)
    # Summaries only — turn text is never exposed to relatives (privacy rule).
    return [{"scenario": s.scenario, "step": s.step, "state": s.state,
             "resolved": bool(s.resolved), "escalated": bool(s.escalated),
             "started_at": s.started_at}
            for s in store.recent_sessions(elder_id, limit=min(limit, 100))]


@app.get("/api/relative/elders/{elder_id}/events")
def relative_elder_events(elder_id: int, limit: int = 50,
                          ident: Identity = Depends(current_identity)):
    _owned_elder(ident, elder_id)
    return [{"type": ev.type, "meta": ev.meta, "at": ev.at}
            for ev in store.recent_events(elder_id, limit=min(limit, 200))]


@app.get("/api/relative/notifications")
def relative_notifications(limit: int = 50, ident: Identity = Depends(current_identity)):
    if ident.role != "relative":
        raise HTTPException(status_code=404)
    return [{"channel": n.channel, "status": n.status, "sent_at": n.sent_at,
             "event_type": n.event_type}
            for n in store.notifications_for_relative(ident.tg_id, limit=min(limit, 200))]


# ---------------- setup wizard / settings ----------------
class SetupBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    language: str = Field(pattern="^(en|ru|de)$")
    phone_os: str = Field(pattern="^(ios|android)$")
    phone_age: str = Field(pattern="^(new|old)$")
    email: str = Field(default="", max_length=200)
    relative_name: str = Field(default="", max_length=120)


@app.post("/api/relative/setup")
def relative_setup(body: SetupBody, ident: Identity = Depends(current_identity)):
    # 'unknown' is allowed: completing the wizard is how a new relative signs up.
    token = store.create_pending_elder(
        name=body.name.strip(), language=body.language, phone_os=body.phone_os,
        phone_age=body.phone_age, relative_name=body.relative_name.strip() or "Family",
        relative_email=body.email.strip(), relative_tg=ident.tg_id)
    bot = _bot_username()
    return {"token": token,
            "link": f"https://t.me/{bot}?start=join_{token}" if bot else None}


class ElderPatch(BaseModel):
    language: Optional[str] = Field(default=None, pattern="^(en|ru|de)$")
    phone_os: Optional[str] = Field(default=None, pattern="^(ios|android)$")
    phone_age: Optional[str] = Field(default=None, pattern="^(new|old)$")


@app.patch("/api/relative/elders/{elder_id}")
def relative_elder_patch(elder_id: int, body: ElderPatch,
                         ident: Identity = Depends(current_identity)):
    _owned_elder(ident, elder_id)
    changed = []
    if body.language:
        store.set_language(elder_id, body.language)
        changed.append(f"language={body.language}")
    if body.phone_os or body.phone_age:
        store.set_profile(elder_id, body.phone_os or "", body.phone_age or "")
        changed.append("profile")
    if changed:
        store.log_event(elder_id, "settings_changed", ", ".join(changed))
    return {"ok": True, "changed": changed}


# ---------------- static SPA ----------------
_dist = pathlib.Path(__file__).resolve().parent.parent.parent / settings.webapp_dist


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(status_code=404)
    candidate = (_dist / path).resolve()
    if path and candidate.is_file() and str(candidate).startswith(str(_dist)):
        return FileResponse(candidate)
    index = _dist / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="webapp not built (run: cd webapp && npm run build)")
