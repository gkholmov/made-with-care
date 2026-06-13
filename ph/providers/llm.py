"""LLM provider interface.

The brain is *conversational but playbook-guided*: the curated playbooks
(ph.core.playbooks) are injected as trusted EXPERT GUIDANCE, and the LLM holds a
real back-and-forth — it reads the elder's replies, looks at screen photos
(vision), and keeps helping. It still must not invent risky steps or ask for
secrets, and a code-enforced safety gate runs before it ever sees a scam.

StubLLM (no API key) is deterministic so the orchestrator stays testable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple
from ph.config import settings


# ---- legacy one-step rephrase (kept for compatibility; orchestrator uses converse) ----
@dataclass
class ComposeRequest:
    instruction: str
    language: str
    elder_name: str = ""
    phone_os: str = ""
    recent_context: str = ""
    photo_present: bool = False


# ---- conversational request/response ----
@dataclass
class ConverseRequest:
    language: str
    elder_name: str = ""
    phone_os: str = ""
    guidance: str = ""                 # relevant playbook steps as reference knowledge
    history: List[Tuple[str, str]] = field(default_factory=list)  # [(role, text)] role: user|assistant
    message: str = ""                  # the elder's latest message
    image_b64: str = ""                # optional screen photo (base64)
    image_mime: str = "image/jpeg"


@dataclass
class ConverseReply:
    text: str
    resolved: bool = False             # True only when the problem is clearly solved


CONVERSE_SYSTEM = (
    "You are a warm, patient technology helper for an older adult{name}. "
    "Always reply in this language code: {language}. Use very simple, plain words and short "
    "sentences — no jargon. Help them solve their phone or computer problem ONE small step at a "
    "time, then stop and wait for their reply. Read what they say and answer their questions. "
    "If they send a photo of their screen, look at it carefully and refer to exactly what you see. "
    "Use the EXPERT GUIDANCE below as your trusted knowledge — follow it and do not invent "
    "unfamiliar or risky technical steps. Be patient and encouraging; it is fine to repeat. "
    "SAFETY: never ask for passwords, verification codes, card or bank numbers; never tell them to "
    "pay, buy gift cards, or give anyone remote access. If someone has asked them to do any of "
    "those, tell them to STOP and check with their family first. "
    "Do not offer to call their family yourself unless they ask or it looks like a scam. "
    "When the problem is clearly solved, say so warmly and set resolved=true."
)

SYSTEM_PERSONA = (  # legacy, for compose()
    "You are a warm, patient tech helper for an older adult. Speak in the user's language. "
    "Use very simple words. Give EXACTLY ONE small step, then stop. Never ask for passwords, "
    "codes, card or bank numbers. Rephrase the instruction faithfully; do not invent steps."
)

_REPLY_TOOL = {
    "name": "respond",
    "description": "Send a reply to the older adult.",
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "The warm, simple reply in the target language."},
            "resolved": {"type": "boolean", "description": "True ONLY if the problem is now clearly solved."},
        },
        "required": ["message", "resolved"],
    },
}


class LLM:
    def compose(self, req: ComposeRequest) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def converse(self, req: ConverseRequest) -> ConverseReply:  # pragma: no cover - interface
        raise NotImplementedError


class StubLLM(LLM):
    """Deterministic, secret-free behavior for local dev + tests."""
    name = "stub"

    def compose(self, req: ComposeRequest) -> str:
        return ("Thanks for the photo. " if req.photo_present else "") + req.instruction

    def converse(self, req: ConverseRequest) -> ConverseReply:
        from ph.core import intent
        if req.message and intent.sentiment(req.message) == "affirmative":
            return ConverseReply("Wonderful — I'm glad that worked!", resolved=True)
        first = next((ln.strip() for ln in (req.guidance or "").splitlines() if ln.strip()),
                     "Let's take a look together.")
        return ConverseReply(("Thanks for the photo. " if req.image_b64 else "") + first, resolved=False)


def _sys(req: ConverseRequest) -> str:
    name = f" named {req.elder_name}" if req.elder_name else ""
    base = CONVERSE_SYSTEM.format(name=name, language=req.language)
    phone = f"\nThey use a {req.phone_os} phone." if req.phone_os else ""
    return f"{base}{phone}\n\nEXPERT GUIDANCE:\n{req.guidance or '(general help)'}"


class OpenAILLM(LLM):
    name = "openai"

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model or "gpt-4o"

    def compose(self, req: ComposeRequest) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": SYSTEM_PERSONA},
                      {"role": "user", "content": req.instruction}],
            temperature=0.3, max_tokens=300)
        return (resp.choices[0].message.content or req.instruction).strip()

    def converse(self, req: ConverseRequest) -> ConverseReply:
        messages = [{"role": "system", "content": _sys(req)}]
        for role, txt in req.history:
            messages.append({"role": role, "content": txt})
        if req.image_b64:
            messages.append({"role": "user", "content": [
                {"type": "text", "text": req.message or "(looking at this screen)"},
                {"type": "image_url",
                 "image_url": {"url": f"data:{req.image_mime};base64,{req.image_b64}"}}]})
        else:
            messages.append({"role": "user", "content": req.message or "(the elder is waiting)"})
        resp = self._client.chat.completions.create(model=self._model, messages=messages,
                                                    temperature=0.4, max_tokens=500)
        return ConverseReply((resp.choices[0].message.content or "").strip(), resolved=False)


class AnthropicLLM(LLM):
    name = "anthropic"

    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model or "claude-3-7-sonnet-latest"

    def compose(self, req: ComposeRequest) -> str:
        msg = self._client.messages.create(
            model=self._model, max_tokens=300, system=SYSTEM_PERSONA,
            messages=[{"role": "user", "content": req.instruction}])
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip() or req.instruction

    def converse(self, req: ConverseRequest) -> ConverseReply:
        messages = []
        for role, txt in req.history:
            messages.append({"role": role, "content": txt})
        content = []
        if req.image_b64:
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": req.image_mime or "image/jpeg", "data": req.image_b64}})
        content.append({"type": "text", "text": req.message or "(the elder is waiting)"})
        messages.append({"role": "user", "content": content})
        msg = self._client.messages.create(
            model=self._model, max_tokens=600, system=_sys(req),
            messages=messages, tools=[_REPLY_TOOL], tool_choice={"type": "tool", "name": "respond"})
        for b in msg.content:
            if getattr(b, "type", "") == "tool_use":
                return ConverseReply(str(b.input.get("message", "")).strip(), bool(b.input.get("resolved")))
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        return ConverseReply(text, resolved=False)
