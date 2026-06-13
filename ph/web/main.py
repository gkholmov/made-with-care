"""Mini App web server entrypoint: `python -m ph.web.main`.

Runs beside the bot process (which stays in long-polling mode) and shares the
same sqlite database through ph.db.store.
"""
from __future__ import annotations
import logging

from ph.config import settings
from ph.db.models import init_db


def main():
    logging.basicConfig(level=settings.log_level,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")
    init_db()
    import uvicorn
    from ph.web.api import app
    logging.getLogger("ph.web").info("Mini App server on port %s (insecure dev auth: %s)",
                                     settings.webapp_port, settings.webapp_insecure_dev)
    uvicorn.run(app, host="0.0.0.0", port=settings.webapp_port, log_level="info")


if __name__ == "__main__":
    main()
