"""
Étape 02 — Comparaison des KPIs
Lance les mêmes prompts sur les configs sélectionnées et compare les résultats.
"""
import os, sys, time, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, list_configs, make_client, choose_mode

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

PROMPTS = [
    "Explique le concept de mémoire dans les chatbots en 2 phrases.",
    "Quelle est la différence entre GPT-4o et GPT-4o-mini ?",
    "Donne-moi 3 avantages du RAG par rapport au fine-tuning.",
    "Qu'est-ce que le context window d'un LLM ?",
    "Explique TPS (Tokens Per Second) et pourquoi c'est important.",
]


def choose_configs() -> list[dict]:
    """Sélection interactive des configs à comparer."""
    configs = list_configs()
    print("Configs disponibles :")
    for i, name in enumerate(configs, 1):
        cfg = CONFIG[name]
        print(f"  {i}. {name} — modèle : {cfg['model']}")
    print("Sélectionnez les configs à comparer (ex: '1 2', '1,2', 'cloud local').")
    print("Appuyez sur Entrée pour toutes les sélectionner.")
    choice = input("Votre choix : ").strip()

    if not choice:
        selected_names = configs
    else:
        parts = choice.replace(",", " ").split()
        selected_names = []
        for p in parts:
            if p.isdigit() and 1 <= int(p) <= len(configs):
                selected_names.append(configs[int(p) - 1])
            elif p in configs:
                selected_names.append(p)
        if not selected_names:
            print("  Sélection invalide, toutes les configs seront utilisées.")
            selected_names = configs

    return [
        {
            "name": name,
            "label": f"{name} ({CONFIG[name]['model']})",
            "model": CONFIG[name]["model"],
            "client": make_client(name),
            "price_input": CONFIG[name]["price_input"],
            "price_output": CONFIG[name]["price_output"],
        }
        for name in selected_names
    ]


def run_benchmark(cfg: dict, prompts: list) -> list:
    results = []
    for i, prompt in enumerate(prompts):
        print(f"  [{i+1}/{len(prompts)}] {prompt[:50]}...")
        start = time.time()
        try:
            response = cfg["client"].chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": "Réponds en français, de façon concise."},
                    {"role": "user", "content": prompt},
                ],
            )
            latency = time.time() - start
            pt = response.usage.prompt_tokens
            ct = response.usage.completion_tokens
            cost = (pt * cfg["price_input"] + ct * cfg["price_output"]) / 1000
            tps = ct / latency if latency > 0 else 0
            results.append({
                "prompt": prompt[:40] + "...",
                "latency": round(latency, 3),
                "tps": round(tps, 1),
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "cost_mc": round(cost * 1000, 4),  # millicents
            })
        except Exception as e:
            print(f"    Erreur: {e}")
            results.append({
                "prompt": prompt[:40] + "...",
                "latency": -1, "tps": -1,
                "prompt_tokens": -1, "completion_tokens": -1, "cost_mc": -1,
            })
    return results


def print_results(cfg: dict, results: list):
    label = cfg["label"]
    is_free = cfg["price_output"] == 0
    print(f"\n=== Résultats : {label} ===")
    headers = ["Prompt", "Latence(s)", "TPS", "Tok. In", "Tok. Out", "Coût(m$)"]
    rows = [
        [
            r["prompt"], r["latency"], r["tps"],
            r["prompt_tokens"], r["completion_tokens"],
            "gratuit" if is_free else r["cost_mc"],
        ]
        for r in results
    ]
    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="rounded_grid"))
    else:
        print(f"{'Latence':>10} {'TPS':>8} {'TokIn':>8} {'TokOut':>8} {'Coût':>10}")
        for r in results:
            cost_str = "  gratuit" if is_free else f"{r['cost_mc']:>10.4f}"
            print(f"{r['latency']:>10.3f} {r['tps']:>8.1f} {r['prompt_tokens']:>8} {r['completion_tokens']:>8} {cost_str}")

    valid = [r for r in results if r["latency"] > 0]
    if valid:
        avg_lat = sum(r["latency"] for r in valid) / len(valid)
        avg_tps = sum(r["tps"] for r in valid) / len(valid)
        cost_str = "gratuit" if is_free else f"{sum(r['cost_mc'] for r in valid):.4f} m$"
        print(f"\nMoyennes → Latence: {avg_lat:.3f}s | TPS: {avg_tps:.1f} | Coût total: {cost_str}")


if __name__ == "__main__":
    print("=== Benchmark Comparatif — Étape 02 ===\n")

    selected = choose_configs()
    all_results = {}

    for cfg in selected:
        print(f"\n--- Benchmark : {cfg['label']} ---")
        results = run_benchmark(cfg, PROMPTS)
        print_results(cfg, results)
        all_results[cfg["name"]] = {"model": cfg["model"], "results": results}

    with open("benchmark_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nRésultats sauvegardés dans benchmark_results.json")
