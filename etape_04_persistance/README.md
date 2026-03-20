# Étape 04 — La Persistance

## Objectif
Faire survivre le chatbot au redémarrage. Comparer SQLite vs JSON.

## Deux approches

### Option A : SQLite (recommandée)
- Multi-sessions
- Multi-utilisateurs simultanés
- Requêtes SQL
- Scalable

### Option B : JSON (simple mais limitée)
- Facile à lire/déboguer
- Un seul utilisateur à la fois
- Corruption possible en concurrent
- Lent avec beaucoup de données

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
```

## Scripts

### persistance_sqlite.py
```bash
python persistance_sqlite.py
```
Au démarrage : choisissez une session existante ou créez-en une nouvelle.
Redémarrez le script → la conversation est restaurée !

### persistance_json.py
```bash
python persistance_json.py
```

### explorer_db.py — Inspectez votre base de données
```bash
python explorer_db.py
```

## Exercice
1. Lancez `persistance_sqlite.py`, dites "Je m'appelle Marie et j'aime le Python"
2. Quittez (quit), relancez → le chatbot se souvient !
3. Créez une 2e session, posez des questions différentes
4. Lancez `explorer_db.py` pour voir les 2 sessions séparées
5. Débat : avec 1000 users simultanés, pourquoi le JSON est catastrophique ?

## Débat en classe
**JSON avec 1000 users simultanés :**
- Race condition : 2 users écrivent en même temps → corruption
- Lecture du fichier entier à chaque requête → lent
- Un seul fichier global → pas de sessions séparées
- Pas de transactions → données partiellement écrites si crash
