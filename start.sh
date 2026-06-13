#!/usr/bin/env bash
# Runs both processes in one container. They share one sqlite file on the volume.
# If EITHER process dies, exit with its status so Fly restarts the whole machine
# (keeps the bot and web server lifecycles tied to a single shared DB).
set -euo pipefail

python -m ph.app.main &        # Telegram bot, long-polling (egress only, no inbound port)
bot_pid=$!

python -m ph.web.main &        # uvicorn: SPA + JSON API + /healthz on 0.0.0.0:$WEBAPP_PORT
web_pid=$!

wait -n
status=$?
kill "$bot_pid" "$web_pid" 2>/dev/null || true
exit "$status"
