"""
Étape 09 — Base de données SQLite
Opérations CRUD pour les messages du chatbot.
"""
import os
import sqlite3
from typing import List
from .models import MessageItem

DB_PATH = os.environ.get("DB_PATH", "chat.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialise la base de données et crée les tables si elles n'existent pas."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                role      TEXT    NOT NULL,
                content   TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")
        conn.commit()


def save_message(session_id: str, role: str, content: str) -> None:
    """Sauvegarde un message en base."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        conn.commit()


def load_history(session_id: str, limit: int = 20) -> List[MessageItem]:
    """Charge les N derniers messages d'une session."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ) ORDER BY created_at ASC
            """,
            (session_id, limit)
        ).fetchall()
    return [MessageItem(role=row["role"], content=row["content"]) for row in rows]


def get_all_sessions() -> List[str]:
    """Retourne la liste de toutes les sessions distinctes."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT session_id FROM messages ORDER BY session_id"
        ).fetchall()
    return [row["session_id"] for row in rows]
