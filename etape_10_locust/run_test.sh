#!/bin/bash
# Étape 10 — Scénarios de test de charge
# Usage: bash run_test.sh [scenario]

HOST=${API_URL:-"http://localhost:8000"}
SCENARIO=${1:-"small"}

echo "=== Test de charge Locust — Étape 10 ==="
echo "Host: $HOST | Scénario: $SCENARIO"
echo ""

case $SCENARIO in
  "smoke")
    echo "Smoke test : 5 users, 30 secondes"
    locust -f locustfile.py --host=$HOST \
      --headless --users 5 --spawn-rate 1 \
      --run-time 30s --csv=results_smoke
    ;;
  "small")
    echo "Test léger : 20 users, 2 minutes"
    locust -f locustfile.py --host=$HOST \
      --headless --users 20 --spawn-rate 2 \
      --run-time 2m --csv=results_small
    ;;
  "medium")
    echo "Test moyen : 50 users, 5 minutes"
    locust -f locustfile.py --host=$HOST \
      --headless --users 50 --spawn-rate 5 \
      --run-time 5m --csv=results_medium
    ;;
  "stress")
    echo "Stress test : 100 users, 10 minutes"
    locust -f locustfile.py --host=$HOST \
      --headless --users 100 --spawn-rate 10 \
      --run-time 10m --csv=results_stress
    ;;
  "ui")
    echo "Mode UI : ouvrez http://localhost:8089"
    locust -f locustfile.py --host=$HOST
    ;;
  *)
    echo "Scénarios disponibles : smoke, small, medium, stress, ui"
    exit 1
    ;;
esac

echo ""
echo "Test terminé. Résultats dans results_${SCENARIO}_stats.csv"
echo "Analysez avec : python analyse_results.py results_${SCENARIO}_stats.csv"
