"""
Étape 02 — Mesurer pour Comprendre
Intégration des KPIs de performance : latence, TPS, coût.
"""
import os, time
from dotenv import load_dotenv
import openai

load_dotenv()

# Configuration
API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MODE = os.environ.get("MODE", "cloud")
LM_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")

# Prix par 1000 tokens (gpt-4o-mini)
PRICE_INPUT = 0.00015   # $0.00015 / 1K tokens input
PRICE_OUTPUT = 0.00060  # $0.00060 / 1K tokens output

if MODE == "local":
    client = openai.OpenAI(base_url=LM_URL, api_key="lm-studio")
else:
    client = openai.OpenAI(api_key=API_KEY)

msgs = [{"role": "system", "content": "Tu es un assistant utile et concis. Réponds en français."}]

# Stats de session
session_stats = {
    "total_requests": 0,
    "total_latency": 0.0,
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "total_cost": 0.0,
    "latencies": [],
}

def calc_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens * PRICE_INPUT + completion_tokens * PRICE_OUTPUT) / 1000

def print_kpis(latency: float, prompt_tokens: int, completion_tokens: int, cost: float):
    tps = completion_tokens / latency if latency > 0 else 0
    print(f"\n  ┌─ KPIs ─────────────────────────────────────────┐")
    print(f"  │ Latence    : {latency:.3f}s", end="")
    status = "✓" if latency < 2 else ("⚠" if latency < 5 else "✗")
    print(f"  {status} (cible < 2s)")
    print(f"  │ TPS        : {tps:.1f} tokens/sec", end="")
    status = "✓" if tps > 30 else "⚠"
    print(f"  {status}")
    print(f"  │ Tokens     : {prompt_tokens} in → {completion_tokens} out")
    print(f"  │ Coût       : ${cost:.6f}")
    print(f"  │ Coût total : ${session_stats['total_cost']:.6f}")
    print(f"  └────────────────────────────────────────────────┘\n")

def print_session_summary():
    n = session_stats["total_requests"]
    if n == 0:
        return
    avg_latency = session_stats["total_latency"] / n
    latencies = sorted(session_stats["latencies"])
    p95_idx = int(0.95 * len(latencies))
    p95 = latencies[min(p95_idx, len(latencies)-1)]
    print(f"\n  ╔═ RÉSUMÉ DE SESSION ({'='*30})╗")
    print(f"  ║ Requêtes        : {n}")
    print(f"  ║ Latence moyenne : {avg_latency:.3f}s")
    print(f"  ║ Latence P95     : {p95:.3f}s")
    print(f"  ║ Tokens totaux   : {session_stats['total_prompt_tokens']} in / {session_stats['total_completion_tokens']} out")
    print(f"  ║ Coût total      : ${session_stats['total_cost']:.6f}")
    print(f"  ╚{'='*42}╝\n")

print(f"=== Chatbot avec KPIs — Étape 02 ===")
print(f"Modèle : {MODEL} | Mode : {MODE}")
print("Tapez 'stats' pour le résumé, 'quit' pour quitter.\n")

try:
    while True:
        q = input("Vous: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        if q.lower() == "stats":
            print_session_summary()
            continue
        if not q:
            continue

        msgs.append({"role": "user", "content": q})

        start = time.time()
        try:
            response = client.chat.completions.create(model=MODEL, messages=msgs)
        except openai.AuthenticationError:
            print("  ✗ Erreur : clé API invalide. Vérifiez OPENAI_API_KEY dans .env\n")
            msgs.pop()
            continue
        except openai.APIConnectionError:
            print("  ✗ Erreur : impossible de se connecter à l'API. Vérifiez votre connexion.\n")
            msgs.pop()
            continue
        except Exception as e:
            print(f"  ✗ Erreur inattendue : {e}\n")
            msgs.pop()
            continue

        latency = time.time() - start
        reply = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        cost = calc_cost(prompt_tokens, completion_tokens)

        msgs.append({"role": "assistant", "content": reply})

        # Mise à jour des stats
        session_stats["total_requests"] += 1
        session_stats["total_latency"] += latency
        session_stats["total_prompt_tokens"] += prompt_tokens
        session_stats["total_completion_tokens"] += completion_tokens
        session_stats["total_cost"] += cost
        session_stats["latencies"].append(latency)

        print(f"IA: {reply}")
        print_kpis(latency, prompt_tokens, completion_tokens, cost)

        # Résumé automatique toutes les 5 requêtes
        if session_stats["total_requests"] % 5 == 0:
            print_session_summary()

except KeyboardInterrupt:
    print("\n\nRésumé final :")
    print_session_summary()
    print("Au revoir !")
