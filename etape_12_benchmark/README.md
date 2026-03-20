# Étape 12 — Benchmark LLM

## Objectif
Comparer objectivement plusieurs modèles LLM sur un jeu d'évaluation standardisé.

## Architecture

```
eval_set.jsonl → benchmark.py → LLM 1, LLM 2, ... → judge.py → results/
```

## Métriques comparées
| Métrique | Description |
|----------|-------------|
| Score LLM-as-Judge | Note 1-10 (pertinence × exactitude × concision) |
| Latence | Temps de réponse par question |
| Latence P95 | 95e percentile |
| Coût total | Tokens × prix du modèle |

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
```

## Lancement
```bash
# Benchmark complet
python benchmark.py

# Analyse des résultats
python analyse.py
```

## Résultats typiques (sur 20 prompts)
| Modèle | Score | Latence | Coût |
|--------|-------|---------|------|
| GPT-4o | 9.1/10 | 1.8s | $0.024 |
| GPT-4o-mini | 8.2/10 | 1.2s | $0.004 |
| Mistral 7B local | 7.1/10 | 0.4s | $0.000 |

## LLM-as-Judge
```python
# Un LLM note les réponses des autres modèles
# Score = (pertinence + exactitude + concision) / 3
```

## Exercice
1. Lancez le benchmark : `python benchmark.py`
2. Analysez : `python analyse.py`
3. Identifiez : quel modèle a le meilleur rapport qualité/prix ?
4. Ajoutez 5 questions dans `eval_set.jsonl`
5. Comparez GPT-4o vs GPT-4o-mini sur vos nouvelles questions
