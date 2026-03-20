"""
Étape 03 — Window Memory
Limite la fenêtre de contexte pour contrôler les coûts.
Concept clé : le Context Window
"""
import os, time
from dotenv import load_dotenv
import openai

load_dotenv()

API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_HISTORY = int(os.environ.get("MAX_HISTORY", "8"))  # 4 paires user+assistant

client = openai.OpenAI(api_key=API_KEY)

SYSTEM = {
    "role": "system",
    "content": (
        "Tu es un assistant utile et concis. Réponds en français. "
        "Si on te demande ce dont tu te souviens, liste les sujets abordés dans la conversation."
    )
}

history = []

def build_context():
    """Retourne la fenêtre glissante des MAX_HISTORY derniers messages."""
    window = history[-MAX_HISTORY:]
    return [SYSTEM] + window

def count_approx_tokens(messages):
    """Estimation rapide : ~4 chars = 1 token."""
    total_chars = sum(len(m["content"]) for m in messages)
    return total_chars // 4

print(f"=== Window Memory — Étape 03 ===")
print(f"Modèle : {MODEL} | Fenêtre : {MAX_HISTORY} messages ({MAX_HISTORY//2} échanges)\n")
print("Commandes : 'fenetre' (voir contexte actuel), 'reset' (vider), 'quit'\n")

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if q.lower() == "fenetre":
            msgs = build_context()
            print(f"\n  Contexte actuel : {len(msgs)-1}/{MAX_HISTORY} messages d'historique")
            print(f"  Tokens estimés  : ~{count_approx_tokens(msgs)}")
            print(f"  Messages en mémoire :")
            for m in history[-MAX_HISTORY:]:
                role = "Vous" if m["role"] == "user" else "IA"
                preview = m["content"][:60] + ("..." if len(m["content"]) > 60 else "")
                print(f"    [{role}] {preview}")
            print()
            continue

        if q.lower() == "reset":
            history.clear()
            print("  Mémoire effacée.\n")
            continue

        if not q:
            continue

        history.append({"role": "user", "content": q})

        # Construction de la fenêtre glissante
        msgs = build_context()
        nb_old = max(0, len(history) - MAX_HISTORY)
        if nb_old > 0:
            print(f"  ⚠  {nb_old} message(s) ancien(s) oublié(s) (hors fenêtre)")

        start = time.time()
        try:
            response = client.chat.completions.create(model=MODEL, messages=msgs)
        except openai.AuthenticationError:
            print("  ✗ Clé API invalide.\n")
            history.pop()
            continue
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")
            history.pop()
            continue

        latency = time.time() - start
        reply = response.choices[0].message.content
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        history.append({"role": "assistant", "content": reply})

        print(f"IA: {reply}")
        print(f"  [contexte: {len(msgs)-1}/{MAX_HISTORY} msgs | {tokens_in}→{tokens_out} tokens | {latency:.2f}s]\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
