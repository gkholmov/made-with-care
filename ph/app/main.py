"""Entrypoint. Long-polling by default; webhook if PUBLIC_BASE_URL is set.

Run:  python -m ph.app.main
"""
from __future__ import annotations
import logging
from ph.config import settings
from ph.db.models import init_db


def main():
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if not settings.telegram_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")
    init_db()
    from ph.adapters.telegram_adapter import build_application
    app = build_application()

    if settings.public_base_url:
        logging.info("Starting in WEBHOOK mode")
        app.run_webhook(
            listen="0.0.0.0", port=8080, url_path="tg",
            webhook_url=f"{settings.public_base_url.rstrip('/')}/tg",
            secret_token=settings.telegram_webhook_secret or None,
        )
    else:
        logging.info("Starting in LONG-POLLING mode")
        app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
