"""Speech-to-text interface. Returns (text, detected_language).

2026 picks for accented/elderly + multilingual: GPT-4o-transcribe (OpenAI) or
Deepgram Nova-3. Stub returns a fixed phrase for offline dev/testing.
"""
from __future__ import annotations
from typing import Tuple
from ph.config import settings


class STT:
    def transcribe(self, audio_bytes: bytes, mime: str = "audio/ogg") -> Tuple[str, str]:  # pragma: no cover
        raise NotImplementedError


class StubSTT(STT):
    name = "stub"

    def transcribe(self, audio_bytes: bytes, mime: str = "audio/ogg") -> Tuple[str, str]:
        # Deterministic placeholder for local dev when no STT key is configured.
        return ("My wifi is not working", "en")


class OpenAISTT(STT):
    name = "openai"

    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = "gpt-4o-transcribe"

    def transcribe(self, audio_bytes: bytes, mime: str = "audio/ogg") -> Tuple[str, str]:
        import io
        f = io.BytesIO(audio_bytes); f.name = "audio.ogg"
        r = self._client.audio.transcriptions.create(model=self._model, file=f)
        lang = getattr(r, "language", "") or ""
        return (r.text.strip(), lang)


class DeepgramSTT(STT):
    name = "deepgram"

    def __init__(self):
        self._key = settings.deepgram_api_key

    def transcribe(self, audio_bytes: bytes, mime: str = "audio/ogg") -> Tuple[str, str]:
        import httpx
        r = httpx.post(
            "https://api.deepgram.com/v1/listen?model=nova-3&detect_language=true&smart_format=true",
            headers={"Authorization": f"Token {self._key}", "Content-Type": mime},
            content=audio_bytes, timeout=60,
        )
        r.raise_for_status()
        d = r.json()["results"]["channels"][0]
        alt = d["alternatives"][0]
        return (alt["transcript"].strip(), d.get("detected_language", "") or "")
