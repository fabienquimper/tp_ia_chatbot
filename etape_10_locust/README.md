# Étape 10 — Test de charge avec Locust

## Objectif
Vérifier que le chatbot tient la charge avec 100 utilisateurs simultanés.

## Installation
```bash
pip install -r requirements.txt
# L'API doit être lancée — utilisez étape 07 ou 08 (sans authentification)
# ⚠ L'étape 09 requiert un token JWT : le locustfile ne gère pas le login,
#   80% des requêtes échoueront avec HTTP 401 si vous pointez sur étape 09+.
```

## Scénarios de test

| Scénario | Users | Durée | Usage |
|----------|-------|-------|-------|
| smoke | 5 | 30s | Vérification rapide |
| small | 20 | 2min | Test quotidien |
| medium | 50 | 5min | Test de validation |
| stress | 100 | 10min | Test de limite |

## Lancement

### Mode UI (dashboard interactif)
```bash
locust -f locustfile.py --host=http://localhost:8000
# Ouvrez http://localhost:8089
```

### Mode headless (CI/CD)
```bash
bash run_test.sh small
```

## Objectifs de performance (SLA)
| KPI | Cible |
|-----|-------|
| Taux d'échec | < 1% |
| Latence P50 | < 2s |
| Latence P95 | < 5s |
| RPS | > 20 |

## Analyse des résultats
```bash
python analyse_results.py results_small_stats.csv
```

## Exercice
1. Lancez le test "small" (20 users, 2 min)
2. Notez le P95 et le taux d'erreur
3. Doublez à 50 users → que se passe-t-il ?
4. Identifiez le goulot d'étranglement (API ? LLM ? DB ?)
