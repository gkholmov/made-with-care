"""Provider factories. Each provider is behind a one-method interface so it can be
swapped (or stubbed) without touching the brain. If no API key/provider is set,
deterministic stubs are returned so the app runs and tests pass with zero secrets."""
from __future__ import annotations
from ph.config import settings
from .llm import LLM, StubLLM, OpenAILLM, AnthropicLLM
from .stt import STT, StubSTT, OpenAISTT, DeepgramSTT
from .tts import TTS, StubTTS, OpenAITTS
from .email import EmailSender, StubEmail, SMTPEmail


def get_llm() -> LLM:
    p = settings.llm_provider
    if p == "openai" and settings.openai_api_key:
        return OpenAILLM()
    if p == "anthropic" and settings.anthropic_api_key:
        return AnthropicLLM()
    return StubLLM()


def get_stt() -> STT:
    p = settings.stt_provider
    if p == "openai" and settings.openai_api_key:
        return OpenAISTT()
    if p == "deepgram" and settings.deepgram_api_key:
        return DeepgramSTT()
    return StubSTT()


def get_tts() -> TTS:
    if settings.tts_provider == "openai" and settings.openai_api_key:
        return OpenAITTS()
    return StubTTS()


def get_email() -> EmailSender:
    if settings.email_provider == "smtp" and settings.smtp_host:
        return SMTPEmail()
    return StubEmail()
