"""The brain. Conversational but playbook-guided.

A code-enforced safety gate runs FIRST (it cannot be overridden by the LLM).
After that the LLM holds a real conversation, using the curated playbooks as
trusted guidance, reading the elder's replies and screen photos. It keeps helping
as long as needed — it never auto-escalates after a fixed number of steps. Family
is brought in only for a code-detected scam/financial risk, when the elder enters
the scam topic, or when the elder explicitly asks.

Pure and adapter-agnostic: takes a normalized inbound message, returns a Reply.
Escalation side-effects go through an injected Notifier (so it's testable)."""
from __future__ import annotations
from dataclasses import dataclass, field

from ph.core import safety, intent, playbooks
from ph.core.i18n import t
from ph.providers.llm import ConverseRequest
from ph.providers import get_llm
from ph.db import store


@dataclass
class Reply:
    text: str
    state: str = "active"        # active | resolved | escalated | safety_stop
    show_call: bool = True       # whether to surface the "Call relative" affordance
    expect_confirm: bool = False  # kept for API compatibility (UI always offers quick replies)
    confirm_kind: str = "worked"  # verb for the "yes" button: worked|see|found|done|open|ask
    choices: list = field(default_factory=list)  # tappable option labels for a choice question


GENERIC_GUIDANCE = (
    "Common older-adult tech problems and safe fixes: getting back online (wifi / restart the "
    "router), resetting a forgotten password via 'Forgot password?', finding an app that moved "
    "after an update (swipe down and search), making text bigger in Settings, and spotting scams. "
    "Keep every step tiny and safe; never ask for passwords, codes, or payment."
)


def _reason_label(safety_class: str) -> str:
    return {"scam": "a possible scam", "financial": "a bank / money account"}.get(safety_class, safety_class)


def handle(elder_id: int, name: str, language: str, text: str,
           modality: str = "text", photo_present: bool = False,
           image_b64: str = "", image_mime: str = "",
           notifier=None, llm=None) -> Reply:
    llm = llm or get_llm()
    text = (text or "").strip()

    # 1) CODE-ENFORCED SAFETY GATE (runs first, cannot be overridden by the LLM)
    safety_class = safety.classify(text)
    if safety_class != "safe":
        sess = store.active_session(elder_id) or store.start_session(elder_id, "safety")
        store.add_turn(sess.id, "in", modality, text)
        relative = store.get_trusted_relative(elder_id)
        ev = store.log_event(elder_id, "safety_stop", f"{safety_class}: {_reason_label(safety_class)}")
        if notifier:
            notifier.escalate(name, _reason_label(safety_class), relative, ev.id)
        store.update_session(sess.id, state="escalated")
        out = t("safety_stop", language, name=(relative.name if relative else "your family"))
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="safety_stop", show_call=True)

    # 2) EXPLICIT REQUEST TO CALL FAMILY
    if text and intent.wants_call(text):
        sess = store.active_session(elder_id) or store.start_session(elder_id, "general")
        store.add_turn(sess.id, "in", modality, text)
        relative = store.get_trusted_relative(elder_id)
        ev = store.log_event(elder_id, "escalation", "elder asked to contact family")
        if notifier:
            notifier.escalate(name, "would like to talk to you", relative, ev.id)
        out = t("escalating", language, name=(relative.name if relative else "your family"))
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="escalated", show_call=True)

    # 3) SESSION + GUIDANCE
    sess = store.active_session(elder_id)
    is_new = sess is None
    if is_new:
        sess = store.start_session(elder_id, intent.route(text) or "general")
    pb = playbooks.get(sess.scenario)
    guidance = "\n".join(s.instruction for s in pb.steps) if pb else GENERIC_GUIDANCE

    # The scam topic is itself a safety concern: alert family once, when it begins.
    if is_new and pb and pb.flag_event == "scam_flag":
        relative = store.get_trusted_relative(elder_id)
        ev = store.log_event(elder_id, "scam_flag", sess.scenario)
        if notifier:
            notifier.escalate(name, "a possible scam", relative, ev.id)

    # 4) HISTORY (prior turns, before storing the current one)
    history = []
    for s in store.recent_turns(sess.id, limit=12):
        role = "user" if s.startswith("in:") else "assistant"
        history.append((role, s.split(":", 1)[1].strip()))

    # 5) CONVERSE
    profile = store.get_profile(elder_id)
    rep = llm.converse(ConverseRequest(
        language=language, elder_name=name, phone_os=profile.get("phone_os", ""),
        guidance=guidance, history=history,
        message=text or "(the elder just opened the helper)",
        image_b64=image_b64, image_mime=image_mime))

    # 6) PERSIST
    store.add_turn(sess.id, "in", modality, text or ("(photo)" if photo_present else ""))
    store.add_turn(sess.id, "out", "text", rep.text)

    # 7) STATE — never auto-escalate; keep helping until solved or the elder asks for family
    if rep.resolved:
        store.update_session(sess.id, state="resolved")
        store.log_event(elder_id, "resolved", sess.scenario)
        return Reply(rep.text, state="resolved", show_call=False)
    return Reply(rep.text, state="active", show_call=True,
                 confirm_kind=rep.confirm_kind, choices=rep.choices)
