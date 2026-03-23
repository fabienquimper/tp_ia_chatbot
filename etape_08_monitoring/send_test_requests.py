"""
Étape 08 — Générateur de trafic de test
Envoie des requêtes pour générer des métriques Prometheus à observer.
"""
import httpx, time, random, sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
NB_REQUESTS = int(sys.argv[2]) if len(sys.argv) > 2 else 50

QUESTIONS = [
    "Qu'est-ce que le RAG ?",
    "Explique le concept de tokenisation.",
    "Quelle est la différence entre GPT-3 et GPT-4 ?",
    "Comment fonctionne l'attention dans les transformers ?",
    "Qu'est-ce qu'un embedding vectoriel ?",
    "Explique le fine-tuning d'un LLM.",
    "Qu'est-ce que le prompt engineering ?",
    "Comment mesurer la latence d'un LLM ?",
    "Qu'est-ce que TPS (Tokens Per Second) ?",
    "Explique la window memory en 2 phrases.",
]

print(f"=== Générateur de trafic — {NB_REQUESTS} requêtes vers {BASE_URL} ===\n")

# Vérification santé
try:
    r = httpx.get(f"{BASE_URL}/health", timeout=5)
    print(f"✓ API disponible : {r.json()}\n")
except Exception as e:
    print(f"✗ API non disponible : {e}")
    sys.exit(1)

stats = {"success": 0, "error": 0, "latencies": []}

for i in range(NB_REQUESTS):
    question = random.choice(QUESTIONS)
    session = f"test-session-{random.randint(1, 5)}"

    try:
        start = time.time()
        response = httpx.post(
            f"{BASE_URL}/chat",
            json={"message": question, "session_id": session},
            timeout=120
        )
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            stats["success"] += 1
            stats["latencies"].append(elapsed)
            print(f"[{i+1:3d}/{NB_REQUESTS}] ✓ {elapsed:.2f}s | {data.get('tokens', '?')} tokens")
        else:
            stats["error"] += 1
            print(f"[{i+1:3d}/{NB_REQUESTS}] ✗ HTTP {response.status_code}")

    except Exception as e:
        stats["error"] += 1
        print(f"[{i+1:3d}/{NB_REQUESTS}] ✗ Erreur: {e}")

    time.sleep(random.uniform(0.5, 2.0))

# Résumé
print(f"\n=== Résumé ===")
print(f"  Succès  : {stats['success']}/{NB_REQUESTS}")
print(f"  Erreurs : {stats['error']}/{NB_REQUESTS}")
if stats["latencies"]:
    lats = sorted(stats["latencies"])
    print(f"  Latence moyenne : {sum(lats)/len(lats):.2f}s")
    print(f"  Latence P50     : {lats[len(lats)//2]:.2f}s")
    print(f"  Latence P95     : {lats[int(0.95*len(lats))]:.2f}s")
print(f"\nOuvrez Grafana : http://localhost:3000 (admin / admin123)")
print(f"Prometheus     : http://localhost:9090")
