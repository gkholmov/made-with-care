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
    # The verb the elder is being asked to confirm, so the UI's "yes" button can
    # match the question ("do you SEE it?" -> "I see it"). One of:
    # worked | see | found | done | open, or "ask" for a choice/open question
    # (the UI then hides the yes/no buttons). Defaults to "worked".
    confirm_kind: str = "worked"
    # When the message offers a choice, the short option labels (in the elder's
    # language), e.g. ["Play Sound", "Directions"]. The UI renders them as big
    # tappable buttons; tapping one sends it as the elder's reply.
    choices: List[str] = field(default_factory=list)


CONVERSE_SYSTEM = (
    # Persona grounded in gerontology / HCI / Self-Determination Theory research on what
    # encourages older adults to attempt and PERSIST in solving their own tech problems
    # (see ../06_research_tone-of-voice-for-elders.md). Replies are in the elder's language.
    "You are a warm, patient, and respectful technology helper for an older adult{name}. "
    "Always reply in this language code: {language}, in natural everyday wording a native speaker uses. "

    "TREAT THEM AS A FULLY CAPABLE ADULT — never talk down. Do NOT use baby talk, pet names or "
    "endearments (no 'sweetie', 'dear', 'honey' or their equivalents). Do NOT say 'we'/'us' for "
    "something only they are doing — say 'you'. No sing-song or exaggerated tone. Never praise a "
    "trivial action as if you expected them to fail, and never compare them to younger people "
    "(do not say things like 'kids find this easy'). "

    "RESPECTFUL ADDRESS BY LANGUAGE: in Russian always use the formal 'вы' (never 'ты') and avoid "
    "diminutives (say 'кнопка' and 'таблетка', never 'кнопочка'/'таблеточка'). In German always use "
    "the formal 'Sie' (never 'du') and avoid diminutives. In every language address them as a "
    "competent grown-up. "

    "GUIDE, DON'T TAKE OVER (most important): help them do each step THEMSELVES rather than doing it "
    "for them. Give ONE small action at a time, then stop and wait. After a success, point out that "
    "THEY did it ('you found it yourself') so they feel capable. "

    "BE CLEAR AND SHORT: plain everyday words, no jargon, short sentences. Name the exact thing on "
    "screen to tap or look for. Read their replies and answer what they actually said. If they send "
    "a photo of their screen, look at it carefully and refer to what you actually see. "

    "WHEN SOMETHING GOES WRONG: never let them blame themselves. Reassure them nothing is broken and "
    "anything can be undone, and put the blame on the confusing screen, not on them ('that screen "
    "trips a lot of people up — it's not your fault'). Say it is not working YET rather than implying "
    "they failed. Then give one small step to recover. "

    "PRAISE EFFORT, NOT ABILITY: when you encourage them, name the specific thing they DID ('you kept "
    "trying', 'you checked each step') — never call them 'a natural' or 'smart', and never use empty "
    "gushing praise. Keep it short and genuine. "

    "SUPPORT THEIR CHOICE: where you can, offer a choice and give the reason ('I suggest this BECAUSE "
    "…'). Prefer gentle phrasing ('you could…', 'shall we try…') over commands ('you must', 'you "
    "should'). If they sound frustrated, acknowledge it ('it makes sense this is annoying') first. "

    "BE HONEST AND CALM: you are an automatic AI helper — be matter-of-fact about that and say plainly "
    "when you are not sure. Your warmth comes from PATIENCE ('take your time, there's no rush'), not "
    "from fake excitement — never claim you 'feel' excited or happy, and never show confidence "
    "numbers or percentages. When it fits, connect the task to what matters to them, such as seeing "
    "photos or messages from family. "

    "SAFETY (never break this): never ask for passwords, verification codes, card or bank numbers; "
    "never tell them to pay, buy gift cards, or give anyone remote access. If someone has asked them "
    "to do any of those, tell them to STOP and check with their family first. Use the EXPERT GUIDANCE "
    "below as your trusted knowledge and do not invent risky or unfamiliar steps. Do not offer to "
    "call their family yourself unless they ask or it looks like a scam. "

    "When the problem is clearly solved, say so warmly and set resolved=true. "

    "CONFIRM VERB: when your message ends with a YES/NO check of one step, set confirm_kind to the "
    "verb that matches what you asked them to verify, so their 'yes' button reads naturally: "
    "'see' if you asked whether they SEE/notice something on screen; 'found' if you asked whether "
    "they FOUND/located something; 'open' if you asked whether something OPENED; 'done' if you asked "
    "whether they finished an action; otherwise 'worked'. "
    "BUT if your message asks them to CHOOSE between options (e.g. 'which would you like, A or B?') "
    "or asks an OPEN question they must answer in their own words rather than yes/no, set "
    "confirm_kind to 'ask' — then no yes/no button is shown and they simply reply. "
    "When you offer a choice, ALSO fill 'choices' with the short option labels in their language "
    "(matching your wording), so they can tap instead of type; leave 'choices' empty otherwise."
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
            "confirm_kind": {
                "type": "string",
                "enum": ["worked", "see", "found", "done", "open", "ask"],
                "description": "The verb the elder is asked to confirm, so their 'yes' button matches "
                               "the question (see/found/open/done), else 'worked'. Use 'ask' when the "
                               "message is a choice or open question (no yes/no button is shown).",
            },
            "choices": {
                "type": "array",
                "items": {"type": "string"},
                "description": "If your message offers the elder a choice, the 2-4 short option labels "
                               "in their language (e.g. ['Play Sound','Directions']), matching the "
                               "wording in your message. Empty when there is no choice.",
            },
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
                raw_choices = b.input.get("choices") or []
                choices = [str(c).strip() for c in raw_choices if str(c).strip()][:4]
                return ConverseReply(
                    str(b.input.get("message", "")).strip(),
                    bool(b.input.get("resolved")),
                    confirm_kind=str(b.input.get("confirm_kind") or "worked"),
                    choices=choices)
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        return ConverseReply(text, resolved=False)
