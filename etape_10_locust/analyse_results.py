"""
Étape 10 — Analyse des résultats Locust
Parse les fichiers CSV et génère un rapport.
"""
import sys, os
import pandas as pd

def analyse(csv_file: str):
    if not os.path.exists(csv_file):
        print(f"✗ Fichier non trouvé : {csv_file}")
        print("  Lancez d'abord un test : bash run_test.sh small")
        return

    df = pd.read_csv(csv_file)
    print(f"\n=== Analyse des résultats : {csv_file} ===\n")

    # Résumé global (ligne "Aggregated")
    agg = df[df["Name"] == "Aggregated"]
    if not agg.empty:
        row = agg.iloc[0]
        total_req = row.get("Request Count", 0)
        failures = row.get("Failure Count", 0)
        fail_rate = failures / total_req * 100 if total_req > 0 else 0
        avg_ms = row.get("Average Response Time", 0)
        p50 = row.get("50%", 0)
        p95 = row.get("95%", 0)
        p99 = row.get("99%", 0)
        rps = row.get("Requests/s", 0)

        print(f"{'─'*50}")
        print(f"RÉSUMÉ GLOBAL")
        print(f"{'─'*50}")
        print(f"  Requêtes totales  : {total_req:,.0f}")
        print(f"  Échecs            : {failures:,.0f} ({fail_rate:.1f}%)")
        print(f"  RPS               : {rps:.1f} req/s")
        print(f"  Latence moyenne   : {avg_ms:.0f} ms")
        print(f"  Latence P50       : {p50:.0f} ms")
        print(f"  Latence P95       : {p95:.0f} ms {'✓' if p95 < 5000 else '✗ > 5s'}")
        print(f"  Latence P99       : {p99:.0f} ms")
        print(f"{'─'*50}\n")

        # Évaluation
        print("ÉVALUATION :")
        checks = [
            ("Taux d'échec < 1%", fail_rate < 1),
            ("Latence P50 < 2s", p50 < 2000),
            ("Latence P95 < 5s", p95 < 5000),
            ("RPS > 5", rps > 5),
        ]
        all_ok = True
        for label, ok in checks:
            status = "✓" if ok else "✗"
            print(f"  {status} {label}")
            if not ok:
                all_ok = False
        print(f"\n{'✓ TOUS LES OBJECTIFS ATTEINTS' if all_ok else '✗ CERTAINS OBJECTIFS NON ATTEINTS'}\n")

    # Par endpoint
    endpoints = df[df["Name"] != "Aggregated"]
    if not endpoints.empty:
        print("PAR ENDPOINT :")
        print(f"  {'Endpoint':20s} {'Req':>8} {'Err':>6} {'Avg(ms)':>10} {'P95(ms)':>10}")
        print(f"  {'─'*60}")
        for _, row in endpoints.iterrows():
            print(f"  {str(row['Name']):20s} {row.get('Request Count',0):>8.0f} "
                  f"{row.get('Failure Count',0):>6.0f} "
                  f"{row.get('Average Response Time',0):>10.0f} "
                  f"{row.get('95%',0):>10.0f}")

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "results_small_stats.csv"
    analyse(csv_file)
