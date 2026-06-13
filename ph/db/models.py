"""Storage schema + connection. Stdlib `sqlite3` only (zero dependencies, runs
anywhere). Matches architecture doc section 6. For production scale, the same
store interface can be re-pointed at Postgres later — see DATABASE_URL.

No credentials, OTPs, or financial data are ever stored (redaction runs before
any user text is written; see ph.core.redaction)."""
from __future__ import annotations
import os
import sqlite3
import threading
from ph.config import settings

_LOCK = threading.Lock()
_conn: sqlite3.Connection | None = None


def _db_path() -> str:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    if url.startswith("sqlite://"):
        return url[len("sqlite://"):] or ":memory:"
    # Non-sqlite URLs (e.g. Postgres) are a post-MVP swap; MVP ships on sqlite.
    return "parent_helper.db"


def conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_db_path(), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys=ON")
        # The bot and web server run as two processes against one DB file. WAL lets
        # them read concurrently; busy_timeout makes a writer wait instead of raising
        # "database is locked". (Each process opens its own _conn, so set per-connection.)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA busy_timeout=5000")
    return _conn


DDL = [
    """CREATE TABLE IF NOT EXISTS elder(
        id INTEGER PRIMARY KEY, telegram_id INTEGER UNIQUE, name TEXT DEFAULT '',
        language TEXT DEFAULT 'en', created_at TEXT DEFAULT (datetime('now')),
        consent_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS relative(
        id INTEGER PRIMARY KEY, telegram_id INTEGER, email TEXT DEFAULT '',
        name TEXT DEFAULT '', language TEXT DEFAULT 'en')""",
    """CREATE TABLE IF NOT EXISTS link(
        id INTEGER PRIMARY KEY, elder_id INTEGER, relative_id INTEGER,
        role TEXT DEFAULT 'trusted', verified_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS device_profile(
        elder_id INTEGER PRIMARY KEY, phone_os TEXT DEFAULT '', phone_age TEXT DEFAULT '',
        notes TEXT DEFAULT '')""",
    """CREATE TABLE IF NOT EXISTS learned_fact(
        id INTEGER PRIMARY KEY, elder_id INTEGER, key TEXT, value TEXT,
        learned_at TEXT DEFAULT (datetime('now')))""",
    """CREATE TABLE IF NOT EXISTS session(
        id INTEGER PRIMARY KEY, elder_id INTEGER, scenario TEXT DEFAULT '', step INTEGER DEFAULT 0,
        state TEXT DEFAULT 'active', started_at TEXT DEFAULT (datetime('now')),
        resolved INTEGER DEFAULT 0, escalated INTEGER DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS turn(
        id INTEGER PRIMARY KEY, session_id INTEGER, direction TEXT, modality TEXT,
        text TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')))""",
    """CREATE TABLE IF NOT EXISTS event(
        id INTEGER PRIMARY KEY, elder_id INTEGER, type TEXT, meta TEXT DEFAULT '',
        at TEXT DEFAULT (datetime('now')))""",
    """CREATE TABLE IF NOT EXISTS notification(
        id INTEGER PRIMARY KEY, relative_id INTEGER, channel TEXT, event_id INTEGER,
        sent_at TEXT DEFAULT (datetime('now')), status TEXT DEFAULT 'sent')""",
]


def init_db():
    c = conn()
    with _LOCK:
        for stmt in DDL:
            c.execute(stmt)
        c.commit()


def reset_db():
    """Tests only: wipe and recreate."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
    p = _db_path()
    if p != ":memory:" and os.path.exists(p):
        os.remove(p)
    init_db()
