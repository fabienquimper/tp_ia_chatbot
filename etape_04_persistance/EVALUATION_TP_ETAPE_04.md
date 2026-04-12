# 🧠 Évaluation — Étape 04 : La Persistance

> ⏱ Durée estimée : 45 min | Niveau : Intermédiaire

## 🎯 Enjeu central

Un chatbot qui oublie tout au redémarrage n'est pas déployable. Cette étape compare
SQLite (robuste, transactionnel, multi-sessions) et JSON (simple mais fragile sous charge).
L'enjeu : comprendre pourquoi les bases de données existent et ce que "concurrent" signifie en prod.

---

## ✅ Checklist de validation

- [ ] J'ai lancé `persistance_sqlite.py`, créé une session, et vérifié la restauration après redémarrage
- [ ] J'ai créé au moins 2 sessions différentes et vérifié leur isolation
- [ ] J'ai lancé `explorer_db.py` et inspecté les tables
- [ ] J'ai lancé `persistance_json.py` et comparé le comportement

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Dans `explorer_db.py`, combien de tables y a-t-il ? Donne le schéma de la table des messages (colonnes et types).

   > _________________________________________________________

2. Après 2 sessions et redémarrage, quelles sessions apparaissent au menu ? Les messages sont-ils bien isolés ?

   > _________________________________________________________

3. Dans le fichier JSON de `persistance_json.py`, à quoi ressemble la structure pour une conversation de 3 échanges ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. SQLite utilise les transactions ACID. Explique ce que signifie "Atomique" dans le contexte d'une écriture de message. Que se passe-t-il si le serveur plante au milieu ?

   > _________________________________________________________

2. Deux utilisateurs écrivent en JSON simultanément. Décris ce qui peut corrompre les données. Quel terme technique désigne ce problème ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Moteur de stockage pour 500 utilisateurs simultanés sur un VPS : SQLite, PostgreSQL ou Redis ? Compare sur 3 critères (simplicité, concurrence, scalabilité) et justifie ton choix.

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Ouvre deux terminaux. Lance `persistance_sqlite.py` dans les deux **simultanément** sur la même session.
Tape un message dans chaque terminal à quelques secondes d'intervalle.
Inspecte avec `explorer_db.py` : les deux messages sont-ils enregistrés ?

**Ce que j'ai observé :**
```
_____________________________________________________________
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **RGPD** : La persistance SQLite répond-elle aux exigences RGPD si le chatbot traite des données personnelles (santé, RH) ? Quelles mesures supplémentaires sont nécessaires (chiffrement, droit à l'effacement) ?
- **Architecture** : Justifiez le choix de SQLite (mono-serveur) vs PostgreSQL (multi-instances). À quel moment faut-il migrer ?

---

## 💡 Pour aller plus loin

- Exécute une requête SQL directement : `sqlite3 chat.db "SELECT * FROM messages LIMIT 10;"`.
- Implémente la suppression d'une session dans le code (droit à l'effacement RGPD).
- Cherche ce qu'est une **migration de schéma** : que se passerait-il si tu ajoutais une colonne `timestamp` sans migration ?
