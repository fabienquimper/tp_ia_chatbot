"""
Étape 02 — Mesurer pour Comprendre
Intégration des KPIs de performance : latence, TPS, coût.
"""
import os, sys, time
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, choose_mode, make_client

mode = choose_mode()
client = make_client(mode)
MODEL = CONFIG[mode]["model"]
price_input = CONFIG[mode]["price_input"]
price_output = CONFIG[mode]["price_output"]

msgs = [{"role": "system", "content": "Tu es un assistant utile et concis. Réponds en français."}]

session_stats = {
    "total_requests": 0,
    "total_latency": 0.0,
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "total_cost": 0.0,
    "latencies": [],
}


def calc_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens * price_input + completion_tokens * price_output) / 1000


def print_kpis(latency: float, prompt_tokens: int, completion_tokens: int, cost: float):
    tps = completion_tokens / latency if latency > 0 else 0
    cost_str = f"${cost:.6f}" if price_output > 0 else "gratuit (local)"
    total_str = f"${session_stats['total_cost']:.6f}" if price_output > 0 else "gratuit (local)"
    print(f"\n  ┌─ KPIs ─────────────────────────────────────────┐")
    print(f"  │ Latence    : {latency:.3f}s", end="")
    status = "✓" if latency < 2 else ("⚠" if latency < 5 else "✗")
    print(f"  {status} (cible < 2s)")
    print(f"  │ TPS        : {tps:.1f} tokens/sec", end="")
    status = "✓" if tps > 30 else "⚠"
    print(f"  {status}")
    print(f"  │ Tokens     : {prompt_tokens} in → {completion_tokens} out")
    print(f"  │ Coût       : {cost_str}")
    print(f"  │ Coût total : {total_str}")
    print(f"  └────────────────────────────────────────────────┘\n")


def print_session_summary():
    n = session_stats["total_requests"]
    if n == 0:
        return
    avg_latency = session_stats["total_latency"] / n
    latencies = sorted(session_stats["latencies"])
    p95_idx = int(0.95 * len(latencies))
    p95 = latencies[min(p95_idx, len(latencies) - 1)]
    cost_str = f"${session_stats['total_cost']:.6f}" if price_output > 0 else "gratuit (local)"
    print(f"\n  ╔═ RÉSUMÉ DE SESSION ({'='*30})╗")
    print(f"  ║ Requêtes        : {n}")
    print(f"  ║ Latence moyenne : {avg_latency:.3f}s")
    print(f"  ║ Latence P95     : {p95:.3f}s")
    print(f"  ║ Tokens totaux   : {session_stats['total_prompt_tokens']} in / {session_stats['total_completion_tokens']} out")
    print(f"  ║ Coût total      : {cost_str}")
    print(f"  ╚{'='*42}╝\n")


print(f"=== Chatbot avec KPIs — Étape 02 ===")
print(f"Modèle : {MODEL} | Mode : {mode}")
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
            print("  ✗ Erreur : clé API invalide. Vérifiez OPENAI_API_KEY dans etape_00_moteur/.env\n")
            msgs.pop()
            continue
        except openai.APIConnectionError:
            print("  ✗ Erreur : impossible de se connecter. Vérifiez que LM Studio est démarré.\n")
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

        session_stats["total_requests"] += 1
        session_stats["total_latency"] += latency
        session_stats["total_prompt_tokens"] += prompt_tokens
        session_stats["total_completion_tokens"] += completion_tokens
        session_stats["total_cost"] += cost
        session_stats["latencies"].append(latency)

        print(f"IA: {reply}")
        print_kpis(latency, prompt_tokens, completion_tokens, cost)

        if session_stats["total_requests"] % 5 == 0:
            print_session_summary()

except KeyboardInterrupt:
    print("\n\nRésumé final :")
    print_session_summary()
    print("Au revoir !")
