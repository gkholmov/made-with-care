"""The brain. Ties safety + intent + playbooks + memory + LLM phrasing into the
one-step-at-a-time loop described in the architecture doc (section 3).

Pure and adapter-agnostic: takes a normalized inbound message, returns a Reply.
Escalation side-effects go through an injected Notifier (so it's testable)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ph.core import safety, intent, playbooks
from ph.core.i18n import t
from ph.providers.llm import ComposeRequest
from ph.providers import get_llm
from ph.db import store


@dataclass
class Reply:
    text: str
    state: str = "active"        # active | resolved | escalated | safety_stop | clarify
    show_call: bool = True       # whether to surface the "Call relative" affordance
    expect_confirm: bool = False  # the step just sent asks "did it work?" -> show ✅/❌ buttons


def expecting_confirmation(elder_id: int) -> bool:
    """True if the elder's last-sent playbook step awaits a yes/no confirmation.
    Recomputed from the store (no in-memory state), so it survives restarts."""
    sess = store.active_session(elder_id)
    if not sess:
        return False
    pb = playbooks.get(sess.scenario)
    return bool(pb and sess.step < len(pb.steps) and pb.steps[sess.step].check)


def _reason_label(safety_class: str) -> str:
    return {"scam": "a possible scam", "financial": "a bank / money account"}.get(safety_class, safety_class)


def handle(elder_id: int, name: str, language: str, text: str,
           modality: str = "text", photo_present: bool = False,
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
        rel_name = relative.name if relative else ""
        out = t("safety_stop", language, name=rel_name or "your family")
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="safety_stop", show_call=True)

    # 2) CONTINUE OR START A SCENARIO
    sess = store.active_session(elder_id)
    profile = store.get_profile(elder_id)
    ctx = " | ".join(store.recent_turns(sess.id)) if sess else ""

    def compose(instruction: str) -> str:
        return llm.compose(ComposeRequest(
            instruction=instruction, language=language, elder_name=name,
            phone_os=profile.get("phone_os", ""), recent_context=ctx, photo_present=photo_present))

    def step_text(pb, idx: int) -> str:
        # Exact, code-generated progress prefix (never the LLM's job): orientation
        # within a multi-step fix matters a lot for elderly users.
        return t("step_progress", language, n=idx + 1, total=len(pb.steps)) + compose(pb.steps[idx].instruction)

    # --- new conversation ---
    if sess is None:
        scenario = intent.route(text)
        sess = store.start_session(elder_id, scenario or "unknown")
        store.add_turn(sess.id, "in", modality, text)
        if not scenario:
            rel = store.get_trusted_relative(elder_id)
            out = t("clarify", language, name=(rel.name if rel else "your family"))
            store.add_turn(sess.id, "out", "text", out)
            return Reply(out, state="clarify", show_call=True)
        pb = playbooks.get(scenario)
        if pb.flag_event:
            store.log_event(elder_id, pb.flag_event, scenario)
        out = step_text(pb, 0)
        store.update_session(sess.id, step=0)
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="active", show_call=True, expect_confirm=pb.steps[0].check)

    # --- continuing an existing conversation ---
    store.add_turn(sess.id, "in", modality, text)
    pb = playbooks.get(sess.scenario)
    if pb is None:  # previous session was 'unknown' -> try to route now
        scenario = intent.route(text)
        if not scenario:
            rel = store.get_trusted_relative(elder_id)
            out = t("clarify", language, name=(rel.name if rel else "your family"))
            store.add_turn(sess.id, "out", "text", out)
            return Reply(out, state="clarify", show_call=True)
        store.set_scenario(sess.id, scenario)
        sess.scenario = scenario
        pb = playbooks.get(scenario)
        if pb.flag_event:
            store.log_event(elder_id, pb.flag_event, scenario)
        out = step_text(pb, 0)
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="active", show_call=True, expect_confirm=pb.steps[0].check)

    cur = pb.steps[sess.step]
    sent = intent.sentiment(text)

    # success on a check step -> resolved
    if cur.check and sent == "affirmative":
        store.update_session(sess.id, state="resolved")
        store.log_event(elder_id, "resolved", pb.name)
        out = t("resolved", language)
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="resolved", show_call=False)

    # advance one step
    nxt = sess.step + 1
    if nxt < len(pb.steps):
        store.update_session(sess.id, step=nxt)
        out = step_text(pb, nxt)
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="active", show_call=True, expect_confirm=pb.steps[nxt].check)

    # exhausted the playbook
    if pb.on_exhaust == "resolved":
        store.update_session(sess.id, state="resolved")
        store.log_event(elder_id, "resolved", pb.name)
        out = t("resolved", language)
        store.add_turn(sess.id, "out", "text", out)
        return Reply(out, state="resolved", show_call=False)

    # escalate
    relative = store.get_trusted_relative(elder_id)
    ev = store.log_event(elder_id, "escalation", pb.name)
    if notifier:
        notifier.escalate(name, pb.name, relative, ev.id)
    store.update_session(sess.id, state="escalated")
    out = t("escalating", language, name=(relative.name if relative else "your family"))
    store.add_turn(sess.id, "out", "text", out)
    return Reply(out, state="escalated", show_call=True)
