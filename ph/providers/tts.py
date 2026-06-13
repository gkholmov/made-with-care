"""Text-to-speech interface. Returns audio bytes (Ogg/Opus, ready for Telegram voice).

2026 pick: gpt-4o-mini-tts (OpenAI) — natural, multilingual, low-latency. Stub returns
empty bytes so callers skip the voice reply in offline dev/testing.
"""
from __future__ import annotations
from ph.config import settings


class TTS:
    def synthesize(self, text: str, language: str = "en") -> bytes:  # pragma: no cover
        raise NotImplementedError


class StubTTS(TTS):
    name = "stub"

    def synthesize(self, text: str, language: str = "en") -> bytes:
        # Empty -> adapter sends no voice reply; keeps offline dev deterministic.
        return b""


class OpenAITTS(TTS):
    name = "openai"

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = "gpt-4o-mini-tts"
        self._voice = settings.tts_voice or "alloy"

    def synthesize(self, text: str, language: str = "en") -> bytes:
        r = self._client.audio.speech.create(
            model=self._model, voice=self._voice, input=text,
            instructions="Speak warmly, slowly and clearly, for an elderly listener.",
            response_format="opus",
        )
        return r.content
