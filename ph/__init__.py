"""Parent Helper — Telegram-first AI tech helper for elders (MVP).

Package layout:
  ph.config         env-driven settings
  ph.providers      swappable LLM / STT / email (stub + real)
  ph.db             SQLAlchemy models + store
  ph.core           i18n, safety, redaction, playbooks, intent, orchestrator (the brain)
  ph.ui             3-button keyboard
  ph.notifications  relative escalation (Telegram + email)
  ph.adapters       Telegram messaging adapter
  ph.app            entrypoint
"""
__version__ = "0.1.0"
