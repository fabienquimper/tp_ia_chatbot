# Étape 02 — Mesurer pour Comprendre

## Objectif
Intégrer des KPIs de performance dans le chatbot dès le début.

## KPIs mesurés
| KPI | Description | Cible |
|-----|-------------|-------|
| Latence | Temps total de réponse | < 2s (P50) |
| TPS | Tokens Per Second | Cloud ~80, Local ~15 |
| Coût/requête | Tokens × prix modèle | < $0.001 |
| Latence P95 | 95e percentile | < 5s |

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
# Éditez .env avec votre clé API
```

## Scripts

### `01_mesurer_kpis.py` — Chatbot avec métriques en temps réel
```bash
python 01_mesurer_kpis.py
```
Commandes disponibles :
- `stats` : affiche le résumé de session
- `quit` : quitte

### `02_kpis_comparatif.py` — Benchmark comparatif
```bash
python 02_kpis_comparatif.py
```

## Exercice
1. Lancez `01_mesurer_kpis.py` et posez 10 questions
2. Tapez `stats` pour voir vos métriques
3. Lancez `02_kpis_comparatif.py` pour voir le benchmark
4. Comparez les résultats cloud vs local (si LM Studio installé)

## Formule de coût
```
coût = (prompt_tokens × $0.00015 + completion_tokens × $0.00060) / 1000
```
Pour gpt-4o-mini. Consultez la page de tarification OpenAI pour les autres modèles.
