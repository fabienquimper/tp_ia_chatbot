# Étape 01 — Le Chatbot Naïf (La Banane)

## Objectif

Créer un chatbot fonctionnel en une dizaine de lignes de Python.
Constater et comprendre le problème fondamental : **l'amnésie du LLM**.

## Le concept de la Banane

Le "problème de la banane" illustre la nature stateless des LLMs :
- Pendant une session : le chatbot semble avoir de la mémoire (grâce à `msgs`)
- Après redémarrage : toute la "mémoire" disparaît

Ce n'est pas un bug — c'est la nature fondamentale des LLMs.
La mémoire est une **illusion** que nous créons côté client.

## Ce que vous apprenez

- L'API `client.chat.completions.create()` et ses paramètres
- Le format `messages` : liste de dicts `{"role": ..., "content": ...}`
- Les rôles : `system`, `user`, `assistant`
- La nature **stateless** du LLM
- Pourquoi l'historique doit être géré côté client

## Installation

```bash
cd etape_01_banane
pip install -r requirements.txt
cp .env.example .env
# Éditez .env avec votre clé API
```

## Utilisation

```bash
python chatbot_naif.py
```

## Expériences à faire

### Expérience 1 — La mémoire en session
1. Lancez le chatbot
2. Dites : `Je m'appelle [votre prénom] et j'adore [un truc]`
3. Demandez : `Quel est mon prénom ?` → Il répond correctement ✓
4. Quittez avec `quit`

### Expérience 2 — L'amnésie après redémarrage
1. Relancez le chatbot
2. Demandez : `Quel est mon prénom ?` → Il ne sait plus ✗
3. CONSTAT : La "mémoire" ne persiste pas entre les sessions

### Expérience 3 — Inspecter le code
Regardez la liste `msgs` dans le code :
```python
msgs = [{"role": "system", "content": "..."}]
# On ajoute user + assistant à chaque tour
msgs.append({"role": "user", "content": q})
msgs.append({"role": "assistant", "content": reply})
```
C'est NOUS qui envoyons tout l'historique à chaque appel.

## Fichiers

```
etape_01_banane/
├── chatbot_naif.py    ← Le chatbot minimal (~10 lignes de logique)
├── prompts_demo.txt   ← Script de démo illustrant l'amnésie
├── .env.example       ← Template d'environnement
├── requirements.txt   ← Dépendances
└── README.md          ← Ce fichier
```

## Question à méditer

> Si le LLM est stateless et qu'on lui envoie l'historique complet à chaque appel,
> que se passe-t-il quand la conversation devient très longue ?

Réponse dans l'**Étape 03 — La Mémoire** !
