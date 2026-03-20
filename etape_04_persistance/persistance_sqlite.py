"""
Étape 04 — Persistance SQLite
Le chatbot survit au redémarrage. Chaque session est identifiée par un UUID.
"""
import os, sqlite3, uuid, time
from datetime import datetime
from dotenv import load_dotenv
import openai

load_dotenv()

API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
DB_PATH = os.environ.get("DB_PATH", "chat.db")
MAX_HISTORY = 8

client = openai.OpenAI(api_key=API_KEY)

# ── Base de données ──────────────────────────────────────────────────────────

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session   TEXT    NOT NULL,
            role      TEXT    NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
            content   TEXT    NOT NULL,
            ts        DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session)")
    conn.commit()
    return conn

def save_message(conn: sqlite3.Connection, session: str, role: str, content: str):
    conn.execute(
        "INSERT INTO messages (session, role, content) VALUES (?, ?, ?)",
        (session, role, content)
    )
    conn.commit()

def load_history(conn: sqlite3.Connection, session: str, limit: int = MAX_HISTORY):
    rows = conn.execute(
        """SELECT role, content FROM messages
           WHERE session = ? AND role != 'system'
           ORDER BY id DESC LIMIT ?""",
        (session, limit)
    ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def list_sessions(conn: sqlite3.Connection):
    rows = conn.execute("""
        SELECT session, COUNT(*) as nb, MIN(ts) as first, MAX(ts) as last
        FROM messages WHERE role = 'user'
        GROUP BY session ORDER BY last DESC LIMIT 10
    """).fetchall()
    return rows

def count_messages(conn: sqlite3.Connection, session: str) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM messages WHERE session = ? AND role != 'system'",
        (session,)
    ).fetchone()[0]

# ── Session management ───────────────────────────────────────────────────────

def choose_session(conn: sqlite3.Connection) -> str:
    sessions = list_sessions(conn)
    print("\n=== Chatbot Persistant — Étape 04 (SQLite) ===\n")

    if sessions:
        print("Sessions existantes :")
        for i, (sid, nb, first, last) in enumerate(sessions):
            print(f"  [{i+1}] {sid[:8]}... | {nb} messages | dernière: {last}")
        print(f"  [N] Nouvelle session")
        print()
        choice = input("Choisissez une session (numéro ou N) : ").strip()
        if choice.upper() != "N" and choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                return sessions[idx][0]

    new_id = str(uuid.uuid4())
    print(f"\nNouvelle session créée : {new_id[:8]}...")
    return new_id

# ── Main ─────────────────────────────────────────────────────────────────────

conn = init_db(DB_PATH)
session_id = os.environ.get("SESSION_ID") or choose_session(conn)

nb_existing = count_messages(conn, session_id)
print(f"\nSession : {session_id[:8]}... | {nb_existing} messages en mémoire")
print("Commandes : 'sessions' (lister), 'session <id>' (changer), 'quit'\n")

SYSTEM_MSG = {"role": "system", "content": "Tu es un assistant utile et concis. Réponds en français."}

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if q.lower() == "sessions":
            for sid, nb, first, last in list_sessions(conn):
                print(f"  {sid[:8]}... | {nb} msgs | {last}")
            print()
            continue

        if q.lower().startswith("session "):
            new_sid = q[8:].strip()
            session_id = new_sid
            nb = count_messages(conn, session_id)
            print(f"  Session changée : {session_id[:8]}... ({nb} messages)\n")
            continue

        if not q:
            continue

        # Charger l'historique depuis SQLite
        history = load_history(conn, session_id, MAX_HISTORY)
        msgs = [SYSTEM_MSG] + history + [{"role": "user", "content": q}]

        save_message(conn, session_id, "user", q)

        start = time.time()
        try:
            response = client.chat.completions.create(model=MODEL, messages=msgs)
        except openai.AuthenticationError:
            print("  ✗ Clé API invalide.\n")
            continue
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")
            continue

        latency = time.time() - start
        reply = response.choices[0].message.content

        save_message(conn, session_id, "assistant", reply)

        total = count_messages(conn, session_id)
        print(f"IA: {reply}")
        print(f"  [{total} msgs sauvegardés | {latency:.2f}s]\n")

except KeyboardInterrupt:
    print("\n\nConversation sauvegardée. Au revoir !")
finally:
    conn.close()
