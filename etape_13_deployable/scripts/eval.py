#!/usr/bin/env python3
"""
Étape 13 — Évaluation end-to-end du chatbot.

Envoie les questions du fichier JSONL à l'API, vérifie les mots-clés attendus
dans la réponse, et affiche un rapport pass/fail avec latences.

Génère également du trafic réel pour alimenter les métriques Prometheus/Grafana.

Usage :
    python scripts/eval.py                        # évaluation complète
    python scripts/eval.py --count 5              # smoke test (5 questions)
    python scripts/eval.py --no-rag --verbose     # sans RAG, réponses complètes
    python scripts/eval.py --url http://prod:8000 # contre un autre serveur
"""
import sys
import json
import time
import argparse
import random
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx requis : pip install httpx")
    sys.exit(1)

# ── ANSI ──────────────────────────────────────────────────────────────────────
GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def get_token(client: httpx.Client, base_url: str, username: str, password: str) -> str:
    resp = client.post(
        f"{base_url}/auth/token",
        data={"username": username, "password": password},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def ask(client: httpx.Client, base_url: str, token: str,
        question: str, use_rag: bool, session_id: str,
        max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        resp = client.post(
            f"{base_url}/chat",
            json={"message": question, "use_rag": use_rag, "session_id": session_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=60.0,
        )
        if resp.status_code == 429:
            wait = 62 if attempt == 0 else 30
            print(f"  {YELLOW}⏳ Rate limit — attente {wait}s...{RESET}", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()  # lève si encore 429 après retries
    return resp.json()


def _normalize(text: str) -> str:
    """Normalise pour la comparaison : minuscules + espaces insécables → espaces."""
    return text.lower().replace("\u00a0", " ").replace("\u202f", " ")


def load_questions(path: Path) -> list[dict]:
    questions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def print_header(n: int, url: str, use_rag: bool, path: Path) -> None:
    print(f"\n{BOLD}{'═'*65}{RESET}")
    print(f"{BOLD}  Évaluation Chatbot — {n} questions{RESET}")
    print(f"{'═'*65}{RESET}")
    print(f"  URL    : {CYAN}{url}{RESET}")
    print(f"  RAG    : {'activé' if use_rag else 'désactivé'}")
    print(f"  Fichier: {path}")
    print(f"{'─'*65}\n")


def print_summary(results: list[dict], latencies: list[float]) -> None:
    total   = len(results)
    passed  = sum(1 for r in results if r["passed"])
    partial = sum(1 for r in results if 0 < r["score"] < 1.0)
    failed  = total - passed - partial

    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0

    print(f"\n{BOLD}{'═'*65}{RESET}")
    pct = passed / total * 100 if total else 0
    color = GREEN if pct >= 80 else YELLOW if pct >= 50 else RED
    print(f"{BOLD}  Résultat : {color}{passed}/{total} PASS{RESET}{BOLD} ({pct:.0f}%){RESET}   "
          f"{YELLOW}{partial} PARTIEL{RESET}   {RED}{failed} FAIL{RESET}")
    print(f"  Latence  : moy={avg_lat:.2f}s  min={min_lat:.2f}s  max={max_lat:.2f}s")

    # Par catégorie
    cats: dict[str, list] = {}
    for r in results:
        cats.setdefault(r["category"] or "autre", []).append(r["score"])
    if len(cats) > 1:
        print(f"\n  {'Catégorie':<18} {'Pass':>6}  Score")
        for cat, scores in sorted(cats.items()):
            cat_pass = sum(1 for s in scores if s >= 1.0)
            avg_s    = sum(scores) / len(scores) * 100
            bar_len  = int(avg_s / 10)
            bar      = "█" * bar_len + "░" * (10 - bar_len)
            print(f"  {cat:<18} {cat_pass:>2}/{len(scores)}  {bar} {avg_s:.0f}%")

    print(f"{'═'*65}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Évaluation end-to-end du chatbot")
    parser.add_argument("--url",       default="http://localhost:8000", help="URL de l'API")
    parser.add_argument("--eval-file", default="data/eval_set.jsonl",   help="Fichier JSONL")
    parser.add_argument("--user",      default="alice",                  help="Utilisateur")
    parser.add_argument("--password",  default="password123",            help="Mot de passe")
    parser.add_argument("--no-rag",    action="store_true",              help="Désactive le RAG")
    parser.add_argument("--count",     type=int, default=0,
                        help="Nombre de questions (0=toutes, utile pour smoke test)")
    parser.add_argument("--verbose",   "-v", action="store_true",        help="Affiche les réponses")
    parser.add_argument("--shuffle",   action="store_true",              help="Ordre aléatoire")
    args = parser.parse_args()

    eval_path = Path(args.eval_file)
    if not eval_path.exists():
        print(f"{RED}Fichier introuvable : {eval_path}{RESET}")
        sys.exit(1)

    questions = load_questions(eval_path)
    if args.shuffle:
        random.shuffle(questions)
    if args.count and args.count < len(questions):
        questions = questions[:args.count]

    use_rag = not args.no_rag
    print_header(len(questions), args.url, use_rag, eval_path)

    results: list[dict]  = []
    latencies: list[float] = []

    with httpx.Client() as client:
        # Authentification
        try:
            token = get_token(client, args.url, args.user, args.password)
            print(f"  {GREEN}✓ Authentification OK{RESET}\n")
        except Exception as exc:
            print(f"  {RED}✗ Authentification échouée : {exc}{RESET}")
            sys.exit(1)

        # Envoi des questions
        for i, q in enumerate(questions, 1):
            qid      = q.get("id", f"q{i:03d}")
            question = q["question"]
            keywords = q.get("expected_keywords", [])
            category = q.get("category", "")
            diff_tag = {"facile": DIM, "moyen": "", "difficile": BOLD}.get(
                q.get("difficulty", ""), "")

            try:
                data     = ask(client, args.url, token, question, use_rag,
                               session_id=f"eval-{qid}")
                reply    = data.get("reply", "")
                latency  = data.get("latency", 0.0)
                rag_used = data.get("rag_used", False)
                n_sources = len(data.get("sources", []))

                norm_reply = _normalize(reply)
                found   = [kw for kw in keywords if _normalize(kw) in norm_reply]
                missing = [kw for kw in keywords if _normalize(kw) not in norm_reply]
                score = len(found) / len(keywords) if keywords else 1.0
                passed = not missing

                latencies.append(latency)

                status_color = GREEN if passed else (YELLOW if score > 0 else RED)
                status_label = "PASS" if passed else ("PART" if score > 0 else "FAIL")
                rag_info = f"[RAG {n_sources}src]" if rag_used else "[no-RAG]"

                print(f"  {diff_tag}[{status_color}{status_label}{RESET}{diff_tag}]"
                      f" {qid} {question[:52]:<52}{RESET}"
                      f" {DIM}{latency:5.2f}s {rag_info}{RESET}")

                if args.verbose or not passed:
                    print(f"         {DIM}→ {reply[:110]}{RESET}")
                    if found:
                        print(f"         {GREEN}✓ {', '.join(found)}{RESET}")
                    if missing:
                        print(f"         {RED}✗ manquants : {', '.join(missing)}{RESET}")

                results.append({"id": qid, "passed": passed, "score": score,
                                "category": category, "latency": latency})

            except Exception as exc:
                print(f"  [{RED}ERR {RESET}] {qid} {question[:52]:<52} {RED}{exc}{RESET}")
                results.append({"id": qid, "passed": False, "score": 0.0,
                                "category": category, "latency": 0.0})

    print_summary(results, latencies)

    passed_total = sum(1 for r in results if r["passed"])
    sys.exit(0 if passed_total == len(results) else 1)


if __name__ == "__main__":
    main()
