"""Subscriber store — SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data/subscribers.db")


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def add_subscriber(email: str) -> bool:
    """Returns True if newly added, False if already exists."""
    conn = _conn()
    try:
        conn.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def list_subscribers() -> list[str]:
    conn = _conn()
    rows = conn.execute("SELECT email FROM subscribers").fetchall()
    conn.close()
    return [r[0] for r in rows]
