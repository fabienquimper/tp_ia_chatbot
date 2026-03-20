"""
Étape 12 — Benchmark LLM
Compare plusieurs modèles sur un jeu d'évaluation standardisé.
"""
import os, sys, time, json
from datetime import datetime
from pathlib import Path
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, make_client

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

from judge import judge_with_llm, judge_with_keywords

# ── Configuration depuis etape_00_moteur/config.py ─────────────────────────
cloud_cfg = CONFIG["cloud"]
local_cfg = CONFIG["local"]
USE_LLM_JUDGE = bool(cloud_cfg["api_key"] and cloud_cfg["api_key"] != "sk-changeme")

# Modèles à comparer — construits depuis CONFIG
MODELS = [
    {
        "name": cloud_cfg["model"],
        "label": f"{cloud_cfg['model']} (Cloud)",
        "client": make_client("cloud") if USE_LLM_JUDGE else None,
        "price_input": cloud_cfg["price_input"],
        "price_output": cloud_cfg["price_output"],
    },
]

# Ajouter le modèle local si LM Studio est accessible
try:
    local_client = make_client("local")
    local_client.models.list()  # Test de connexion
    MODELS.append({
        "name": local_cfg["model"],
        "label": f"{local_cfg['model']} (Local)",
        "client": local_client,
        "price_input": local_cfg["price_input"],
        "price_output": local_cfg["price_output"],
    })
    print(f"✓ LM Studio disponible : {local_cfg['model']}")
except Exception:
    print("⚠ LM Studio non disponible — benchmark cloud uniquement")

EVAL_FILE = "eval_set.jsonl"
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

def load_eval_set(filepath: str) -> list:
    questions = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions

def call_model(client, model_name: str, question: str) -> tuple[str, float, int, int]:
    """
    Appelle un modèle et retourne (réponse, latence, tokens_in, tokens_out).
    """
    if client is None:
        return ("Modèle non disponible (pas de clé API)", 0.0, 0, 0)

    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en IA et développement logiciel. Réponds en français, de façon concise et précise (max 150 mots)."},
                {"role": "user", "content": question}
            ],
            max_tokens=300,
            timeout=30
        )
        latency = time.time() - start
        answer = response.choices[0].message.content
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens
        return answer, latency, tokens_in, tokens_out
    except Exception as e:
        latency = time.time() - start
        return (f"ERREUR: {e}", latency, 0, 0)

def calc_cost(model_cfg: dict, tokens_in: int, tokens_out: int) -> float:
    return (tokens_in * model_cfg["price_input"] + tokens_out * model_cfg["price_output"]) / 1000

def run_benchmark():
    print(f"\n=== Benchmark LLM — Étape 12 ===")
    print(f"Modèles : {[m['label'] for m in MODELS]}")
    print(f"Évaluation : LLM-as-Judge={'✓' if USE_LLM_JUDGE else '✗ (mots-clés)'}\n")

    questions = load_eval_set(EVAL_FILE)
    print(f"{len(questions)} questions chargées depuis {EVAL_FILE}\n")

    all_results = []

    for model_cfg in MODELS:
        print(f"\n{'─'*60}")
        print(f"Modèle : {model_cfg['label']}")
        print(f"{'─'*60}")

        model_results = []
        total_cost = 0.0

        for i, qa in enumerate(questions):
            question = qa["question"]
            print(f"  [{i+1:2d}/{len(questions)}] {question[:60]}...", end="", flush=True)

            answer, latency, tokens_in, tokens_out = call_model(
                model_cfg["client"], model_cfg["name"], question
            )
            cost = calc_cost(model_cfg, tokens_in, tokens_out)
            total_cost += cost

            # Évaluation
            if USE_LLM_JUDGE and not answer.startswith("ERREUR"):
                scores = judge_with_llm(question, answer)
            else:
                scores = judge_with_keywords(question, answer, qa.get("expected_keywords", []))

            result = {
                "model": model_cfg["label"],
                "model_name": model_cfg["name"],
                "question_id": qa["id"],
                "question": question,
                "category": qa.get("category", "general"),
                "difficulty": qa.get("difficulty", "moyen"),
                "answer": answer,
                "latency": round(latency, 3),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": round(cost, 6),
                **scores
            }
            model_results.append(result)
            all_results.append(result)

            print(f" ✓ {latency:.1f}s | score={scores['score']:.1f}")
            time.sleep(0.5)  # Éviter le rate limit

        # Résumé par modèle
        valid = [r for r in model_results if not r["answer"].startswith("ERREUR")]
        if valid:
            avg_score = sum(r["score"] for r in valid) / len(valid)
            avg_latency = sum(r["latency"] for r in valid) / len(valid)
            print(f"\n  → Score moyen : {avg_score:.1f}/10")
            print(f"  → Latence moy : {avg_latency:.2f}s")
            print(f"  → Coût total  : ${total_cost:.4f}")

    # Sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"benchmark_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "models": [m["label"] for m in MODELS],
            "nb_questions": len(questions),
            "judge_method": "llm" if USE_LLM_JUDGE else "keywords",
            "results": all_results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Résultats sauvegardés : {output_file}")

    return all_results

def print_summary(results: list):
    """Affiche le tableau de comparaison final."""
    if not results:
        return

    print(f"\n{'═'*70}")
    print("TABLEAU COMPARATIF FINAL")
    print(f"{'═'*70}")

    # Grouper par modèle
    models = {}
    for r in results:
        model = r["model"]
        if model not in models:
            models[model] = []
        models[model].append(r)

    summary_rows = []
    for model, model_results in models.items():
        valid = [r for r in model_results if not r["answer"].startswith("ERREUR")]
        if not valid:
            continue
        avg_score = sum(r["score"] for r in valid) / len(valid)
        avg_latency = sum(r["latency"] for r in valid) / len(valid)
        total_cost = sum(r["cost_usd"] for r in valid)
        p95_idx = int(0.95 * len(valid))
        latencies_sorted = sorted(r["latency"] for r in valid)
        p95_lat = latencies_sorted[min(p95_idx, len(latencies_sorted)-1)]

        summary_rows.append([
            model,
            f"{avg_score:.1f}/10",
            f"{avg_latency:.2f}s",
            f"{p95_lat:.2f}s",
            f"${total_cost:.4f}",
            f"{len(valid)}/{len(model_results)}"
        ])

    headers = ["Modèle", "Score moy.", "Latence moy.", "Latence P95", "Coût total", "Succès"]
    if HAS_TABULATE:
        print(tabulate(summary_rows, headers=headers, tablefmt="rounded_grid"))
    else:
        print(f"{'Modèle':30s} {'Score':>10} {'Lat.moy':>10} {'P95':>10} {'Coût':>12}")
        for row in summary_rows:
            print(f"{row[0]:30s} {row[1]:>10} {row[2]:>10} {row[3]:>10} {row[4]:>12}")

    print(f"\n{'═'*70}")
    print("RECOMMANDATION :")
    if len(summary_rows) > 1:
        best_quality = max(summary_rows, key=lambda x: float(x[1].split("/")[0]))
        best_cost = min(summary_rows, key=lambda x: float(x[4].replace("$", "")))
        print(f"  Meilleure qualité : {best_quality[0]}")
        print(f"  Meilleur coût     : {best_cost[0]}")
    print(f"{'═'*70}\n")

if __name__ == "__main__":
    results = run_benchmark()
    print_summary(results)
