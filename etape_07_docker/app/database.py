import sqlite3
import os
from typing import List
from .models import MessageItem

DB_PATH = os.environ.get("DB_PATH", "chat.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session   TEXT    NOT NULL,
            role      TEXT    NOT NULL,
            content   TEXT    NOT NULL,
            ts        DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session)")
    conn.commit()
    conn.close()

def save_message(session_id: str, role: str, content: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (session, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()

def load_history(session_id: str, limit: int = 8) -> List[MessageItem]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT role, content FROM messages
           WHERE session = ? AND role != 'system'
           ORDER BY id DESC LIMIT ?""",
        (session_id, limit)
    ).fetchall()
    conn.close()
    return [MessageItem(role=r["role"], content=r["content"]) for r in reversed(rows)]

def get_all_sessions():
    conn = get_connection()
    rows = conn.execute("""
        SELECT session, COUNT(*) as nb, MAX(ts) as last_ts
        FROM messages WHERE role = 'user'
        GROUP BY session ORDER BY last_ts DESC
    """).fetchall()
    conn.close()
    return [{"session_id": r["session"], "message_count": r["nb"], "last_message": r["last_ts"]} for r in rows]
