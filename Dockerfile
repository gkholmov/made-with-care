# ---- Stage 1: build the React SPA ----
FROM node:20-slim AS webapp
WORKDIR /webapp
COPY webapp/package.json webapp/package-lock.json* ./
RUN npm ci
COPY webapp/ ./
RUN npm run build      # -> /webapp/dist

# ---- Stage 2: python runtime (bot + web server in one container) ----
FROM python:3.11-slim AS runtime
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code + launcher
COPY ph/ ./ph/
COPY start.sh ./start.sh
RUN chmod +x ./start.sh

# Built SPA into the path ph/web/api.py expects: <repo root>/webapp/dist
COPY --from=webapp /webapp/dist ./webapp/dist

# tini as PID1: reaps zombies and forwards signals to both child processes.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/start.sh"]
