# Parent Helper Bot (MVP)

Telegram-first, voice-first AI helper that walks an older adult through everyday tech
problems one small step at a time, and escalates to a trusted relative (Telegram + email)
when needed. Built to the plan in `../03_mvp_development_plan.md` and `../04_mvp_technical_architecture.md`.

## What it does
- Elder talks to a single Telegram "Helper" contact via **3 big buttons**: 🎙️ tell the problem (voice), 📷 show the screen (photo), 📞 call a relative.
- **Voice input** → speech-to-text → on-rails guidance from 5 curated playbooks: **wifi, password, os_update, setup, scam**.
- **Voice replies**: voice messages are answered with audio too (gpt-4o-mini-tts), alongside the text.
- **Code-enforced safety gate**: never asks for passwords/codes/money; bank/scam situations stop and notify the relative.
- **Multilingual** (QA: ru / en / de); the LLM phrases each step in the elder's language.
- **Privacy**: secrets are redacted before storage; `/delete` wipes all data; short retention.

## Architecture (lean, swappable)
```
Telegram ──> adapter ──> orchestrator(brain) ──> playbooks + safety + LLM-phrasing
                                  │
                          sqlite store (Postgres later)
                                  │
                       escalation: Telegram + email
```
Providers (LLM / STT / email) sit behind one-method interfaces; with no API keys set,
deterministic **stubs** run so everything works offline.

## Run the tests (no dependencies needed)
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Try it offline (simulated conversation, no Telegram)
```bash
PYTHONPATH=. python3 scripts/smoke.py
```

## Run the real bot
```bash
cp .env.example .env          # fill in TELEGRAM_BOT_TOKEN (+ optional LLM/STT/email keys)
pip install -r requirements.txt
python -m ph.app.main         # long-polling (or set PUBLIC_BASE_URL for webhook)
```
Relative sends `/setup`; the bot returns a personal link for the elder to tap.

## Telegram Mini App (two faces, one URL)

One web app served by FastAPI; the server decides the face from the validated
Telegram identity: **elders** get a huge-button visual home (topic taps continue in
the chat via `sendData`), **relatives** get a dashboard (setup wizard, activity feed,
scam alerts, settings). A relative only ever sees elders linked to them, and no
conversation text is exposed — event/session summaries only.

```bash
# 1. Build the frontend
cd webapp && npm install && npm run build && cd ..

# 2. Start the web server (port 8081) next to the bot
.venv/bin/python -m ph.web.main

# 3. Expose it over HTTPS (Mini Apps require a public https URL)
cloudflared tunnel --url http://localhost:8081     # or ngrok http 8081

# 4. Put the printed https URL into .env and restart the bot
#    WEBAPP_URL=https://...           (also set TELEGRAM_BOT_USERNAME=made_with_care_bot)
python -m ph.app.main
```
With `WEBAPP_URL` set, elders get a "🟢 Open my helper" keyboard button and the bot
menu button opens the dashboard. Without it, nothing changes.

Frontend dev loop without Telegram:
```bash
WEBAPP_INSECURE_DEV=1 .venv/bin/python -m ph.web.main          # accepts "Authorization: dev <tg_id>"
cd webapp && VITE_MOCK_TMA=1 VITE_DEV_TG_ID=2002 npm run dev   # proxies /api to :8081
```

API tests need the venv (`.venv/bin/python -m unittest discover -s tests`); on system
Python they skip automatically so the zero-dependency suite stays green.

See `../05_implementation_and_launch_plan.md` for full launch steps, the test/security
checklist, and go-live.
