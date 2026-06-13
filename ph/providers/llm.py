"""LLM provider interface.

The brain stays *on rails*: the correct tech steps come from curated playbooks
(ph.core.playbooks). The LLM's job is narrow and safe — take a canonical English
step instruction and (a) phrase it warmly in the elder's language, one step at a
time, and (b) interpret a screen photo. It does NOT invent tech procedures.

StubLLM (no API key) returns the canonical English text verbatim, which makes the
whole orchestrator deterministic and testable. Real providers translate/rephrase
into RU/DE/etc. at runtime.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from ph.config import settings


@dataclass
class ComposeRequest:
    instruction: str          # canonical English step content (from playbook)
    language: str             # target language code, e.g. "ru"
    elder_name: str = ""
    phone_os: str = ""        # "ios" | "android" | ""
    recent_context: str = ""  # short, redacted recent turns
    photo_present: bool = False


SYSTEM_PERSONA = (
    "You are a warm, patient tech helper for an older adult. "
    "Speak in the user's language. Use very simple, plain words — no jargon. "
    "Give EXACTLY ONE small step, then stop and wait. Keep it short. "
    "Be encouraging; it is fine to repeat. "
    "Never ask for passwords, verification codes, card or bank numbers. "
    "Never tell them to pay, send gift cards, or give anyone remote access. "
    "Rephrase the provided instruction faithfully; do not invent new technical steps."
)


class LLM:
    def compose(self, req: ComposeRequest) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class StubLLM(LLM):
    """Deterministic: returns the canonical instruction unchanged (English).
    Used for local dev + tests so behavior is reproducible with no secrets."""
    name = "stub"

    def compose(self, req: ComposeRequest) -> str:
        text = req.instruction
        if req.photo_present:
            text = "Thanks for the photo. " + text
        return text


class OpenAILLM(LLM):
    name = "openai"

    def __init__(self):
        from openai import OpenAI  # lazy import
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.llm_model or "gpt-4o"

    def compose(self, req: ComposeRequest) -> str:
        user = (
            f"Target language: {req.language}. Elder name: {req.elder_name or 'unknown'}. "
            f"Phone: {req.phone_os or 'unknown'}. "
            f"Recent context: {req.recent_context or 'none'}. "
            f"Photo attached: {req.photo_present}.\n\n"
            f"Instruction to convey (rephrase warmly, one step, in the target language):\n{req.instruction}"
        )
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": SYSTEM_PERSONA},
                      {"role": "user", "content": user}],
            temperature=0.3, max_tokens=300,
        )
        return (resp.choices[0].message.content or req.instruction).strip()


class AnthropicLLM(LLM):
    name = "anthropic"

    def __init__(self):
        import anthropic  # lazy import
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.llm_model or "claude-3-7-sonnet-latest"

    def compose(self, req: ComposeRequest) -> str:
        user = (
            f"Target language: {req.language}. Elder name: {req.elder_name or 'unknown'}. "
            f"Phone: {req.phone_os or 'unknown'}. Recent context: {req.recent_context or 'none'}. "
            f"Photo attached: {req.photo_present}.\n\nInstruction (rephrase warmly, one step, "
            f"in the target language):\n{req.instruction}"
        )
        msg = self._client.messages.create(
            model=self._model, max_tokens=300, system=SYSTEM_PERSONA,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip() or req.instruction
