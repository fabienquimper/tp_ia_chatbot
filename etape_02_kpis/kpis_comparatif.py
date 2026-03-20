"""
Étape 02 — Comparaison des KPIs
Lance les mêmes prompts sur différentes configurations et compare.
"""
import os, time, json
from dotenv import load_dotenv
import openai
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

load_dotenv()

PROMPTS = [
    "Explique le concept de mémoire dans les chatbots en 2 phrases.",
    "Quelle est la différence entre GPT-4o et GPT-4o-mini ?",
    "Donne-moi 3 avantages du RAG par rapport au fine-tuning.",
    "Qu'est-ce que le context window d'un LLM ?",
    "Explique TPS (Tokens Per Second) et pourquoi c'est important.",
]

PRICE_INPUT = 0.00015
PRICE_OUTPUT = 0.00060

def run_benchmark(client, model_name, prompts):
    results = []
    for i, prompt in enumerate(prompts):
        print(f"  [{i+1}/{len(prompts)}] {prompt[:50]}...")
        start = time.time()
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "Réponds en français, de façon concise."},
                    {"role": "user", "content": prompt}
                ]
            )
            latency = time.time() - start
            pt = response.usage.prompt_tokens
            ct = response.usage.completion_tokens
            cost = (pt * PRICE_INPUT + ct * PRICE_OUTPUT) / 1000
            tps = ct / latency if latency > 0 else 0
            results.append({
                "prompt": prompt[:40] + "...",
                "latency": round(latency, 3),
                "tps": round(tps, 1),
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "cost": round(cost * 1000, 4),  # en millicents
            })
        except Exception as e:
            print(f"    Erreur: {e}")
            results.append({
                "prompt": prompt[:40] + "...",
                "latency": -1, "tps": -1,
                "prompt_tokens": -1, "completion_tokens": -1, "cost": -1
            })
    return results

def print_results(model_name, results):
    print(f"\n=== Résultats pour {model_name} ===")
    headers = ["Prompt", "Latence(s)", "TPS", "Tokens In", "Tokens Out", "Coût(m$)"]
    rows = [[r["prompt"], r["latency"], r["tps"], r["prompt_tokens"], r["completion_tokens"], r["cost"]] for r in results]
    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="rounded_grid"))
    else:
        print(f"{'Latence':>10} {'TPS':>8} {'TokIn':>8} {'TokOut':>8} {'Coût':>10}")
        for r in results:
            print(f"{r['latency']:>10.3f} {r['tps']:>8.1f} {r['prompt_tokens']:>8} {r['completion_tokens']:>8} {r['cost']:>10.4f}")

    valid = [r for r in results if r["latency"] > 0]
    if valid:
        avg_lat = sum(r["latency"] for r in valid) / len(valid)
        avg_tps = sum(r["tps"] for r in valid) / len(valid)
        total_cost = sum(r["cost"] for r in valid)
        print(f"\nMoyennes → Latence: {avg_lat:.3f}s | TPS: {avg_tps:.1f} | Coût total: {total_cost:.4f} m$\n")

if __name__ == "__main__":
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("MODEL", "gpt-4o-mini")

    if not api_key or api_key == "sk-changeme":
        print("⚠  Pas de clé API. Définissez OPENAI_API_KEY dans .env")
        print("   Mode démonstration avec données simulées.\n")
        import random
        simulated = []
        for p in PROMPTS:
            lat = round(random.uniform(0.8, 2.5), 3)
            ct = random.randint(50, 150)
            simulated.append({
                "prompt": p[:40] + "...",
                "latency": lat, "tps": round(ct / lat, 1),
                "prompt_tokens": random.randint(30, 80),
                "completion_tokens": ct,
                "cost": round((30 * PRICE_INPUT + ct * PRICE_OUTPUT), 4)
            })
        print_results(f"{model} (simulé)", simulated)
    else:
        client = openai.OpenAI(api_key=api_key)
        print(f"Benchmark sur {len(PROMPTS)} prompts avec {model}...")
        results = run_benchmark(client, model, PROMPTS)
        print_results(model, results)
        with open("benchmark_results.json", "w") as f:
            json.dump({"model": model, "results": results}, f, indent=2)
        print("Résultats sauvegardés dans benchmark_results.json")
