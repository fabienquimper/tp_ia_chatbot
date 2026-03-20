"""
Étape 04 — Explorateur de base de données
Permet de visualiser et analyser les conversations stockées.
"""
import os, sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ.get("DB_PATH", "chat.db")

def open_db():
    if not os.path.exists(DB_PATH):
        print(f"✗ Base de données introuvable : {DB_PATH}")
        print("  Lancez d'abord persistance_sqlite.py pour créer la base.")
        return None
    return sqlite3.connect(DB_PATH)

def show_menu():
    print("\n=== Explorateur de Base de Données ===")
    print("1. Lister les sessions")
    print("2. Afficher une session complète")
    print("3. Statistiques globales")
    print("4. Supprimer une session")
    print("5. Exporter une session en JSON")
    print("0. Quitter")
    return input("\nChoix : ").strip()

def list_sessions(conn):
    rows = conn.execute("""
        SELECT session, COUNT(*) as nb,
               SUM(CASE WHEN role='user' THEN 1 ELSE 0 END) as user_msgs,
               MIN(ts) as first_msg, MAX(ts) as last_msg
        FROM messages
        GROUP BY session
        ORDER BY last_msg DESC
    """).fetchall()
    if not rows:
        print("  Aucune session trouvée.")
        return []
    print(f"\n{'Session':>12} | {'Total':>6} | {'User':>6} | {'Première':>20} | {'Dernière':>20}")
    print("-" * 75)
    for sid, nb, um, first, last in rows:
        print(f"  {sid[:10]}... | {nb:>6} | {um:>6} | {first:>20} | {last:>20}")
    return [r[0] for r in rows]

def show_session(conn, session_id):
    rows = conn.execute(
        "SELECT role, content, ts FROM messages WHERE session = ? ORDER BY id",
        (session_id,)
    ).fetchall()
    if not rows:
        print(f"  Session '{session_id[:8]}...' introuvable.")
        return
    print(f"\n=== Session {session_id[:8]}... ({len(rows)} messages) ===")
    for role, content, ts in rows:
        prefix = "Vous" if role == "user" else ("IA" if role == "assistant" else "System")
        print(f"\n[{ts}] {prefix}:")
        print(f"  {content}")

def show_stats(conn):
    total_sessions = conn.execute("SELECT COUNT(DISTINCT session) FROM messages").fetchone()[0]
    total_msgs = conn.execute("SELECT COUNT(*) FROM messages WHERE role != 'system'").fetchone()[0]
    total_user = conn.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'").fetchone()[0]
    print(f"\n=== Statistiques globales ===")
    print(f"  Sessions totales : {total_sessions}")
    print(f"  Messages totaux  : {total_msgs}")
    print(f"  Messages user    : {total_user}")
    print(f"  Messages IA      : {total_msgs - total_user}")
    if total_sessions > 0:
        print(f"  Moy. msgs/session: {total_msgs // total_sessions}")

def export_session(conn, session_id):
    import json
    rows = conn.execute(
        "SELECT role, content, ts FROM messages WHERE session = ? ORDER BY id",
        (session_id,)
    ).fetchall()
    data = {
        "session_id": session_id,
        "messages": [{"role": r, "content": c, "timestamp": t} for r, c, t in rows]
    }
    filename = f"export_{session_id[:8]}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Session exportée dans {filename}")

def main():
    conn = open_db()
    if conn is None:
        return

    sessions = []
    while True:
        choice = show_menu()
        if choice == "0":
            break
        elif choice == "1":
            sessions = list_sessions(conn)
        elif choice == "2":
            if not sessions:
                sessions = list_sessions(conn)
            sid = input("ID de session (début suffisant) : ").strip()
            # Recherche partielle
            full_sessions = conn.execute(
                "SELECT DISTINCT session FROM messages WHERE session LIKE ?",
                (sid + "%",)
            ).fetchall()
            if full_sessions:
                show_session(conn, full_sessions[0][0])
            else:
                print("  Session non trouvée.")
        elif choice == "3":
            show_stats(conn)
        elif choice == "4":
            sid = input("ID de session à supprimer : ").strip()
            conn.execute("DELETE FROM messages WHERE session LIKE ?", (sid + "%",))
            conn.commit()
            print(f"  Session supprimée.")
        elif choice == "5":
            sid = input("ID de session à exporter : ").strip()
            full = conn.execute(
                "SELECT DISTINCT session FROM messages WHERE session LIKE ?",
                (sid + "%",)
            ).fetchone()
            if full:
                export_session(conn, full[0])
            else:
                print("  Session non trouvée.")

    conn.close()
    print("Au revoir !")

if __name__ == "__main__":
    main()
