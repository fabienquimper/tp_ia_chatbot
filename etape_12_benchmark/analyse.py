"""
Étape 12 — Analyse des résultats de benchmark
Génère des rapports détaillés depuis les fichiers JSON.
"""
import sys, json
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

RESULTS_DIR = Path("results")

def load_latest_results() -> dict:
    """Charge le dernier fichier de résultats."""
    files = sorted(RESULTS_DIR.glob("benchmark_*.json"))
    if not files:
        print("✗ Aucun résultat trouvé. Lancez d'abord : python benchmark.py")
        return None
    latest = files[-1]
    print(f"Chargement : {latest}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f)

def analyse_by_category(results: list):
    """Analyse les scores par catégorie."""
    categories = {}
    for r in results:
        cat = r.get("category", "general")
        if cat not in categories:
            categories[cat] = {"scores": [], "models": {}}
        categories[cat]["scores"].append(r["score"])
        model = r["model"]
        if model not in categories[cat]["models"]:
            categories[cat]["models"][model] = []
        categories[cat]["models"][model].append(r["score"])

    print("\n=== Par catégorie ===")
    for cat, data in sorted(categories.items()):
        avg = sum(data["scores"]) / len(data["scores"])
        print(f"\n  {cat.upper()} (moy: {avg:.1f}/10)")
        for model, scores in data["models"].items():
            model_avg = sum(scores) / len(scores)
            print(f"    {model:40s} : {model_avg:.1f}/10")

def analyse_by_difficulty(results: list):
    """Analyse les scores par difficulté."""
    difficulties = {}
    for r in results:
        diff = r.get("difficulty", "moyen")
        if diff not in difficulties:
            difficulties[diff] = []
        difficulties[diff].append(r["score"])

    print("\n=== Par difficulté ===")
    for diff in ["facile", "moyen", "difficile"]:
        if diff in difficulties:
            scores = difficulties[diff]
            avg = sum(scores) / len(scores)
            print(f"  {diff:10s} : {avg:.1f}/10 ({len(scores)} questions)")

def main():
    data = load_latest_results()
    if not data:
        return

    results = data["results"]
    print(f"\n=== Analyse du Benchmark ===")
    print(f"Date        : {data['timestamp']}")
    print(f"Modèles     : {', '.join(data['models'])}")
    print(f"Questions   : {data['nb_questions']}")
    print(f"Méthode     : {data['judge_method']}")

    analyse_by_category(results)
    analyse_by_difficulty(results)

    # Top 5 meilleures réponses
    valid = [r for r in results if not r["answer"].startswith("ERREUR")]
    if valid:
        top5 = sorted(valid, key=lambda r: r["score"], reverse=True)[:5]
        print(f"\n=== Top 5 meilleures réponses ===")
        for i, r in enumerate(top5):
            print(f"\n  [{i+1}] Score: {r['score']:.1f}/10 | {r['model']}")
            print(f"  Q: {r['question'][:80]}")
            print(f"  R: {r['answer'][:120]}...")

if __name__ == "__main__":
    main()
