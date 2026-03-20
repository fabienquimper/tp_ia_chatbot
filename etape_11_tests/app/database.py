import sqlite3
import os
from typing import List
from .models import MessageItem

DB_PATH = os.environ.get("DB_PATH", "chat.db")

def get_db_path():
    return os.environ.get("DB_PATH", "chat.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            session TEXT    NOT NULL,
            role    TEXT    NOT NULL,
            content TEXT    NOT NULL,
            ts      DATETIME DEFAULT CURRENT_TIMESTAMP
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

def count_messages(session_id: str) -> int:
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE session = ?", (session_id,)
    ).fetchone()[0]
    conn.close()
    return count
