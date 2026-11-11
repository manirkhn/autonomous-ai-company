"""SQLite storage for WhatsApp messages, contacts, material requests and bot state."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core.db import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_whatsapp_tables() -> None:
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS wa_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wa_message_id TEXT UNIQUE,
        direction TEXT NOT NULL,           -- in | out
        contact TEXT NOT NULL,             -- phone, international, no +
        contact_name TEXT,
        msg_type TEXT,                     -- text | image | document | ...
        body TEXT,
        media_id TEXT,
        raw TEXT,
        created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_wa_messages_contact ON wa_messages(contact, created_at);
    CREATE TABLE IF NOT EXISTS wa_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kind TEXT NOT NULL,                -- material_request | punch_card | enquiry
        contact TEXT NOT NULL,
        contact_name TEXT,
        details TEXT,
        media_id TEXT,
        status TEXT NOT NULL DEFAULT 'new',-- new | quoting | awaiting_approval | approved | closed
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS wa_state (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    conn.commit()
    conn.close()


def save_message(direction: str, contact: str, body: Optional[str], msg_type: str = "text",
                 wa_message_id: Optional[str] = None, contact_name: Optional[str] = None,
                 media_id: Optional[str] = None, raw: Optional[Dict[str, Any]] = None) -> bool:
    """Returns False if this inbound message id was already stored (Meta retries webhooks)."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO wa_messages (wa_message_id, direction, contact, contact_name, msg_type, body, media_id, raw, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (wa_message_id, direction, contact, contact_name, msg_type, body, media_id,
             json.dumps(raw) if raw else None, _now()),
        )
        conn.commit()
        return True
    except Exception as exc:  # duplicate wa_message_id
        if "UNIQUE" in str(exc):
            return False
        raise
    finally:
        conn.close()


def recent_messages(contact: str, limit: int = 12) -> List[Dict[str, Any]]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT direction, body, msg_type, created_at FROM wa_messages WHERE contact=? ORDER BY id DESC LIMIT ?",
        (contact, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def outbound_count_since(contact: str, minutes: int) -> int:
    since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    conn = get_connection()
    n = conn.execute(
        "SELECT COUNT(*) FROM wa_messages WHERE contact=? AND direction='out' AND created_at>=?",
        (contact, since),
    ).fetchone()[0]
    conn.close()
    return n


def last_outbound_body(contact: str) -> Optional[str]:
    conn = get_connection()
    row = conn.execute(
        "SELECT body FROM wa_messages WHERE contact=? AND direction='out' ORDER BY id DESC LIMIT 1",
        (contact,),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def add_request(kind: str, contact: str, details: str, contact_name: Optional[str] = None,
                media_id: Optional[str] = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO wa_requests (kind, contact, contact_name, details, media_id, created_at) VALUES (?,?,?,?,?,?)",
        (kind, contact, contact_name, details, media_id, _now()),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def list_requests(status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM wa_requests WHERE status=? ORDER BY id DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM wa_requests ORDER BY id DESC LIMIT 200").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_state(key: str, default: Optional[str] = None) -> Optional[str]:
    conn = get_connection()
    row = conn.execute("SELECT value FROM wa_state WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default


def set_state(key: str, value: str) -> None:
    conn = get_connection()
    conn.execute("INSERT INTO wa_state (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                 (key, value))
    conn.commit()
    conn.close()
