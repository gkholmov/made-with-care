"""Environment-driven configuration. No secrets are hard-coded."""
from __future__ import annotations
import os
import pathlib
from dataclasses import dataclass


def _load_dotenv() -> None:
    """Minimal .env loader (stdlib only). Already-set env vars take precedence,
    so tests and deployment env stay in control."""
    path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.split(" #", 1)[0].strip().strip("'\"")  # drop inline comments
        if v:
            os.environ.setdefault(k.strip(), v)


_load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass(frozen=True)
class Settings:
    telegram_token: str = _get("TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = _get("TELEGRAM_WEBHOOK_SECRET")
    public_base_url: str = _get("PUBLIC_BASE_URL")

    llm_provider: str = _get("LLM_PROVIDER", "stub")
    openai_api_key: str = _get("OPENAI_API_KEY")
    anthropic_api_key: str = _get("ANTHROPIC_API_KEY")
    llm_model: str = _get("LLM_MODEL")

    stt_provider: str = _get("STT_PROVIDER", "stub")
    deepgram_api_key: str = _get("DEEPGRAM_API_KEY")

    tts_provider: str = _get("TTS_PROVIDER", "stub")
    tts_voice: str = _get("TTS_VOICE", "alloy")

    email_provider: str = _get("EMAIL_PROVIDER", "stub")
    smtp_host: str = _get("SMTP_HOST")
    smtp_port: int = int(_get("SMTP_PORT", "587") or "587")
    smtp_user: str = _get("SMTP_USER")
    smtp_password: str = _get("SMTP_PASSWORD")
    email_from: str = _get("EMAIL_FROM", "helper@parent-helper.app")

    database_url: str = _get("DATABASE_URL", "sqlite:///parent_helper.db")
    retention_days: int = int(_get("DATA_RETENTION_DAYS", "30") or "30")
    log_level: str = _get("LOG_LEVEL", "INFO")

    # Telegram Mini App (webapp). Empty WEBAPP_URL = all webapp features disabled.
    webapp_url: str = _get("WEBAPP_URL")
    webapp_port: int = int(_get("WEBAPP_PORT", "8081") or "8081")
    webapp_dist: str = _get("WEBAPP_DIST", "webapp/dist")
    webapp_auth_max_age: int = int(_get("WEBAPP_AUTH_MAX_AGE", "3600") or "3600")
    webapp_insecure_dev: bool = _get("WEBAPP_INSECURE_DEV") == "1"
    bot_username: str = _get("TELEGRAM_BOT_USERNAME")

    # Supported QA launch languages (system is multilingual via the LLM).
    supported_langs: tuple = ("en", "ru", "de")
    default_lang: str = "en"


settings = Settings()
