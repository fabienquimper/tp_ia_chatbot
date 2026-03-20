"""
Étape 04 — Persistance JSON (version simple)
Alternative simple à SQLite. Montre les limites avec plusieurs utilisateurs.
"""
import os, sys, json, time
from datetime import datetime
from pathlib import Path
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, choose_mode, make_client

mode = choose_mode()
client = make_client(mode)
MODEL = CONFIG[mode]["model"]
HISTORY_FILE = os.environ.get("HISTORY_FILE", "historique.json")
MAX_HISTORY = 8

def load_history_json(filepath: str) -> list:
    """Charge l'historique depuis le fichier JSON."""
    if Path(filepath).exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("messages", [])
        except (json.JSONDecodeError, KeyError):
            return []
    return []

def save_history_json(filepath: str, history: list):
    """Sauvegarde l'historique dans le fichier JSON."""
    data = {
        "last_updated": datetime.now().isoformat(),
        "message_count": len(history),
        "messages": history
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Chargement initial
history = load_history_json(HISTORY_FILE)
print(f"=== Chatbot Persistant — Étape 04 (JSON) ===")
print(f"Fichier : {HISTORY_FILE} | {len(history)} messages chargés\n")
print("⚠  LIMITATION : ce fichier est partagé entre tous les utilisateurs !")
print("   Pour plusieurs users simultanés → utilisez SQLite (persistance_sqlite.py)\n")

SYSTEM = {"role": "system", "content": "Tu es un assistant utile et concis. Réponds en français."}

try:
    while True:
        q = input("Vous: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue

        history.append({"role": "user", "content": q})

        # Fenêtre glissante
        window = history[-MAX_HISTORY:]
        msgs = [SYSTEM] + window

        start = time.time()
        try:
            response = client.chat.completions.create(model=MODEL, messages=msgs)
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")
            history.pop()
            continue

        latency = time.time() - start
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})

        # Sauvegarde immédiate
        save_history_json(HISTORY_FILE, history)

        print(f"IA: {reply}")
        print(f"  [{len(history)} msgs sauvegardés dans {HISTORY_FILE} | {latency:.2f}s]\n")

except KeyboardInterrupt:
    save_history_json(HISTORY_FILE, history)
    print(f"\n\nHistorique sauvegardé ({len(history)} messages). Au revoir !")
