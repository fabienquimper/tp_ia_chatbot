# Étape 03 — La Mémoire Tampon

## Objectif
Simuler la mémoire avec une Window Memory et comprendre le Context Window.

## Concept clé : Context Window
| Modèle | Contexte max | Recommandation |
|--------|-------------|----------------|
| GPT-4o | 128K tokens | Fenêtre de 20 échanges |
| GPT-4o-mini | 128K tokens | Fenêtre de 10 échanges |
| Phi-3 local | 4K tokens | Fenêtre de 4 échanges |

**Règle d'or :** `coût ∝ nombre de tokens envoyés`

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
```

## Scripts

### memory_window.py — Fenêtre glissante simple
```bash
python memory_window.py
```
Commandes : `fenetre`, `reset`, `quit`

### memory_summary.py — Résumé automatique (avancé)
```bash
MAX_HISTORY=6 python memory_summary.py
```

## Exercice
1. Lancez `memory_window.py` avec `MAX_HISTORY=4`
2. Posez 10 questions sur des sujets différents
3. Tapez `fenetre` pour voir ce qui est retenu
4. Vérifiez que les premières questions sont oubliées
5. Comparez avec `memory_summary.py` : que retient-il ?

## Variable d'environnement
```
MAX_HISTORY=8   # nombre de messages conservés (4 échanges)
```
