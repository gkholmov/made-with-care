"""Repository helpers over sqlite3. Same public API the orchestrator/adapter rely on.
All user-authored text is redacted before storage."""
from __future__ import annotations
import datetime as dt
import uuid
from types import SimpleNamespace
from typing import Optional
from ph.db.models import conn, _LOCK
from ph.core.redaction import redact


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _ex(sql: str, params: tuple = ()) -> int:
    c = conn()
    with _LOCK:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid


def _q(sql: str, params: tuple = ()):
    return conn().execute(sql, params).fetchall()


def _one(sql: str, params: tuple = ()):
    rows = _q(sql, params)
    return rows[0] if rows else None


# ---- elders / onboarding ----
def get_or_create_elder(telegram_id: int, name: str = "", language: str = "en") -> SimpleNamespace:
    row = _one("SELECT * FROM elder WHERE telegram_id=?", (telegram_id,))
    if not row:
        eid = _ex("INSERT INTO elder(telegram_id,name,language) VALUES(?,?,?)",
                  (telegram_id, name, language))
        return SimpleNamespace(id=eid, telegram_id=telegram_id, name=name, language=language)
    return SimpleNamespace(**dict(row))


def set_language(elder_id: int, language: str):
    _ex("UPDATE elder SET language=? WHERE id=?", (language, elder_id))


def create_pending_elder(name: str, language: str, phone_os: str, phone_age: str,
                         relative_name: str, relative_email: str,
                         relative_tg: Optional[int]) -> str:
    token = uuid.uuid4().hex[:12]
    eid = _ex("INSERT INTO elder(telegram_id,name,language) VALUES(NULL,?,?)", (name, language))
    _ex("INSERT INTO device_profile(elder_id,phone_os,phone_age,notes) VALUES(?,?,?,?)",
        (eid, phone_os, phone_age, f"token:{token}"))
    rid = _ex("INSERT INTO relative(telegram_id,email,name,language) VALUES(?,?,?,?)",
              (relative_tg, relative_email, relative_name, language))
    _ex("INSERT INTO link(elder_id,relative_id,role,verified_at) VALUES(?,?,?,?)",
        (eid, rid, "trusted", _now()))
    return token


def claim_elder(token: str, telegram_id: int) -> Optional[SimpleNamespace]:
    row = _one("SELECT elder_id FROM device_profile WHERE notes=?", (f"token:{token}",))
    if not row:
        return None
    eid = row["elder_id"]
    existing = _one("SELECT * FROM elder WHERE telegram_id=?", (telegram_id,))
    if existing and existing["id"] != eid:
        # This Telegram account already has an elder row (e.g. /setup was run again).
        # Merge the pending profile into the existing row instead of violating the
        # UNIQUE telegram_id constraint: the fresh setup wins for name/language/phone.
        pending = _one("SELECT * FROM elder WHERE id=?", (eid,))
        prof = _one("SELECT * FROM device_profile WHERE elder_id=?", (eid,))
        old = eid
        eid = existing["id"]
        _ex("UPDATE elder SET name=?, language=?, consent_at=? WHERE id=?",
            (pending["name"], pending["language"], _now(), eid))
        if prof:
            set_profile(eid, prof["phone_os"], prof["phone_age"])
        _ex("UPDATE link SET elder_id=? WHERE elder_id=?", (eid, old))  # newest link wins
        _ex("DELETE FROM device_profile WHERE elder_id=?", (old,))
        _ex("DELETE FROM elder WHERE id=?", (old,))
    else:
        _ex("UPDATE elder SET telegram_id=?, consent_at=? WHERE id=?", (telegram_id, _now(), eid))
        _ex("UPDATE device_profile SET notes='' WHERE elder_id=?", (eid,))
    e = _one("SELECT * FROM elder WHERE id=?", (eid,))
    return SimpleNamespace(**dict(e))


def set_consent(elder_id: int):
    _ex("UPDATE elder SET consent_at=? WHERE id=?", (_now(), elder_id))


def set_profile(elder_id: int, phone_os: str = "", phone_age: str = "", notes: str = ""):
    if _one("SELECT 1 FROM device_profile WHERE elder_id=?", (elder_id,)):
        _ex("UPDATE device_profile SET phone_os=COALESCE(NULLIF(?,''),phone_os),"
            "phone_age=COALESCE(NULLIF(?,''),phone_age),notes=COALESCE(NULLIF(?,''),notes) "
            "WHERE elder_id=?", (phone_os, phone_age, notes, elder_id))
    else:
        _ex("INSERT INTO device_profile(elder_id,phone_os,phone_age,notes) VALUES(?,?,?,?)",
            (elder_id, phone_os, phone_age, notes))


def link_relative(elder_id: int, name: str, email: str = "", telegram_id: Optional[int] = None,
                  language: str = "en") -> SimpleNamespace:
    rid = _ex("INSERT INTO relative(telegram_id,email,name,language) VALUES(?,?,?,?)",
              (telegram_id, email, name, language))
    lid = _ex("INSERT INTO link(elder_id,relative_id,role,verified_at) VALUES(?,?,?,?)",
              (elder_id, rid, "trusted", _now()))
    return SimpleNamespace(id=lid, relative_id=rid)


def get_trusted_relative(elder_id: int) -> Optional[SimpleNamespace]:
    row = _one("SELECT r.* FROM relative r JOIN link l ON l.relative_id=r.id "
               "WHERE l.elder_id=? AND l.role='trusted' ORDER BY l.id DESC", (elder_id,))
    return SimpleNamespace(**dict(row)) if row else None


# ---- profile / facts ----
def remember_fact(elder_id: int, key: str, value: str):
    _ex("INSERT INTO learned_fact(elder_id,key,value) VALUES(?,?,?)",
        (elder_id, key, redact(value)[:300]))


def get_facts(elder_id: int) -> dict:
    return {r["key"]: r["value"] for r in _q("SELECT key,value FROM learned_fact WHERE elder_id=?",
                                             (elder_id,))}


def get_profile(elder_id: int) -> dict:
    row = _one("SELECT phone_os,phone_age FROM device_profile WHERE elder_id=?", (elder_id,))
    return {"phone_os": row["phone_os"] if row else "", "phone_age": row["phone_age"] if row else ""}


# ---- sessions / turns ----
def active_session(elder_id: int) -> Optional[SimpleNamespace]:
    row = _one("SELECT * FROM session WHERE elder_id=? AND state='active' ORDER BY id DESC",
               (elder_id,))
    return SimpleNamespace(**dict(row)) if row else None


def start_session(elder_id: int, scenario: str) -> SimpleNamespace:
    sid = _ex("INSERT INTO session(elder_id,scenario,step,state) VALUES(?,?,0,'active')",
              (elder_id, scenario))
    return SimpleNamespace(id=sid, elder_id=elder_id, scenario=scenario, step=0, state="active")


def update_session(session_id: int, step: Optional[int] = None, state: Optional[str] = None):
    if step is not None:
        _ex("UPDATE session SET step=? WHERE id=?", (step, session_id))
    if state is not None:
        _ex("UPDATE session SET state=?, resolved=?, escalated=? WHERE id=?",
            (state, 1 if state == "resolved" else 0, 1 if state == "escalated" else 0, session_id))


def set_scenario(session_id: int, scenario: str):
    _ex("UPDATE session SET scenario=?, step=0 WHERE id=?", (scenario, session_id))


def add_turn(session_id: int, direction: str, modality: str, text: str):
    safe = redact(text) if direction == "in" else text
    _ex("INSERT INTO turn(session_id,direction,modality,text) VALUES(?,?,?,?)",
        (session_id, direction, modality, safe[:4000]))


def recent_turns(session_id: int, limit: int = 6) -> list[str]:
    rows = _q("SELECT direction,text FROM turn WHERE session_id=? ORDER BY id DESC LIMIT ?",
              (session_id, limit))
    return [f"{r['direction']}: {r['text']}" for r in reversed(rows)]


# ---- events / notifications ----
def log_event(elder_id: int, type_: str, meta: str = "") -> SimpleNamespace:
    eid = _ex("INSERT INTO event(elder_id,type,meta) VALUES(?,?,?)",
              (elder_id, type_, redact(meta)[:1000]))
    return SimpleNamespace(id=eid, type=type_)


def log_notification(relative_id: int, channel: str, event_id: Optional[int], status: str = "sent"):
    _ex("INSERT INTO notification(relative_id,channel,event_id,status) VALUES(?,?,?,?)",
        (relative_id, channel, event_id, status))


# ---- GDPR / retention ----
def delete_elder_data(telegram_id: int) -> bool:
    row = _one("SELECT id FROM elder WHERE telegram_id=?", (telegram_id,))
    if not row:
        return False
    eid = row["id"]
    sids = [r["id"] for r in _q("SELECT id FROM session WHERE elder_id=?", (eid,))]
    for sid in sids:
        _ex("DELETE FROM turn WHERE session_id=?", (sid,))
    rids = [r["relative_id"] for r in _q("SELECT relative_id FROM link WHERE elder_id=?", (eid,))]
    _ex("DELETE FROM session WHERE elder_id=?", (eid,))
    _ex("DELETE FROM learned_fact WHERE elder_id=?", (eid,))
    _ex("DELETE FROM event WHERE elder_id=?", (eid,))
    _ex("DELETE FROM device_profile WHERE elder_id=?", (eid,))
    _ex("DELETE FROM link WHERE elder_id=?", (eid,))
    for rid in rids:
        _ex("DELETE FROM relative WHERE id=?", (rid,))
    _ex("DELETE FROM elder WHERE id=?", (eid,))
    return True


def purge_old_turns(retention_days: int) -> int:
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=retention_days)).isoformat()
    rows = _q("SELECT id FROM turn WHERE created_at < ?", (cutoff,))
    for r in rows:
        _ex("DELETE FROM turn WHERE id=?", (r["id"],))
    return len(rows)


# ---- test/inspection helpers ----
def events(elder_id: int) -> list[str]:
    return [r["type"] for r in _q("SELECT type FROM event WHERE elder_id=? ORDER BY id", (elder_id,))]


def all_turn_text() -> str:
    return " ".join(r["text"] for r in _q("SELECT text FROM turn", ()))


def notification_channels() -> set:
    return {r["channel"] for r in _q("SELECT channel FROM notification", ())}


def find_elder_by_tg(telegram_id: int) -> Optional[SimpleNamespace]:
    row = _one("SELECT * FROM elder WHERE telegram_id=?", (telegram_id,))
    return SimpleNamespace(**dict(row)) if row else None


# ---- webapp / relative dashboard (read-mostly) ----
def get_elder(elder_id: int) -> Optional[SimpleNamespace]:
    row = _one("SELECT * FROM elder WHERE id=?", (elder_id,))
    return SimpleNamespace(**dict(row)) if row else None


def find_relatives_by_tg(telegram_id: int) -> list:
    """All relative rows for this Telegram account (one is inserted per /setup run)."""
    return [SimpleNamespace(**dict(r)) for r in
            _q("SELECT * FROM relative WHERE telegram_id=? ORDER BY id DESC", (telegram_id,))]


def elders_for_relative(relative_tg: int) -> list:
    """Elders linked (role='trusted') to any relative row of this Telegram account.
    The webapp must never show elders outside this list."""
    rows = _q("SELECT DISTINCT e.* FROM elder e "
              "JOIN link l ON l.elder_id=e.id "
              "JOIN relative r ON r.id=l.relative_id "
              "WHERE r.telegram_id=? AND l.role='trusted' ORDER BY e.id DESC", (relative_tg,))
    return [SimpleNamespace(**dict(r)) for r in rows]


def relative_owns_elder(relative_tg: int, elder_id: int) -> bool:
    return _one("SELECT 1 FROM link l JOIN relative r ON r.id=l.relative_id "
                "WHERE r.telegram_id=? AND l.elder_id=? AND l.role='trusted'",
                (relative_tg, elder_id)) is not None


def recent_sessions(elder_id: int, limit: int = 20) -> list:
    rows = _q("SELECT id,scenario,step,state,resolved,escalated,started_at FROM session "
              "WHERE elder_id=? ORDER BY id DESC LIMIT ?", (elder_id, limit))
    return [SimpleNamespace(**dict(r)) for r in rows]


def recent_events(elder_id: int, limit: int = 50) -> list:
    rows = _q("SELECT type,meta,at FROM event WHERE elder_id=? ORDER BY id DESC LIMIT ?",
              (elder_id, limit))
    return [SimpleNamespace(**dict(r)) for r in rows]


def last_event_at(elder_id: int) -> Optional[str]:
    row = _one("SELECT at FROM event WHERE elder_id=? ORDER BY id DESC", (elder_id,))
    return row["at"] if row else None


def notifications_for_relative(relative_tg: int, limit: int = 50) -> list:
    rows = _q("SELECT n.channel,n.status,n.sent_at,e.type AS event_type "
              "FROM notification n JOIN relative r ON r.id=n.relative_id "
              "LEFT JOIN event e ON e.id=n.event_id "
              "WHERE r.telegram_id=? ORDER BY n.id DESC LIMIT ?", (relative_tg, limit))
    return [SimpleNamespace(**dict(r)) for r in rows]


def pending_join_token(elder_id: int) -> Optional[str]:
    """The join token for a not-yet-claimed elder ('' once claimed)."""
    row = _one("SELECT notes FROM device_profile WHERE elder_id=?", (elder_id,))
    if row and row["notes"].startswith("token:"):
        return row["notes"][6:]
    return None
