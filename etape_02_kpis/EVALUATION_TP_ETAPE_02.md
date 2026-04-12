# 🧠 Évaluation — Étape 02 : Mesurer pour Comprendre (KPIs)

> ⏱ Durée estimée : 30 min | Niveau : Débutant

## 🎯 Enjeu central

On ne pilote pas ce qu'on ne mesure pas. Cette étape introduit les 4 KPIs fondamentaux
d'un LLM en production : latence, TPS, coût par requête, P95.
L'enjeu : prendre des décisions techniques basées sur des chiffres, pas des intuitions.

---

## ✅ Checklist de validation

- [ ] J'ai lancé `mesurer_kpis.py` et posé au moins 5 questions
- [ ] J'ai tapé `stats` et lu le résumé de session
- [ ] J'ai noté mon P95 personnel
- [ ] J'ai lancé `kpis_comparatif.py` et obtenu des résultats chiffrés

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Quel TPS (tokens/seconde) as-tu observé ? Est-il dans la plage attendue pour le cloud (~80 TPS) ?

   > _________________________________________________________

2. Quel était ton coût moyen par requête en dollars ? Combien coûterait 10 000 requêtes/jour ?

   > _________________________________________________________

3. Quelle est la différence entre ta latence **moyenne** et ton **P95** ? Sur combien de requêtes ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. Pourquoi le P95 est-il plus utile que la moyenne ? Donne un exemple où la moyenne serait trompeuse.

   > _________________________________________________________

2. La formule est `(prompt_tokens × $0.00015 + completion_tokens × $0.00060) / 1000`. Pourquoi les tokens de complétion sont-ils 4× plus chers ? Qu'est-ce que ça implique pour la taille du system prompt ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Définis un SLA réaliste pour ce chatbot en production : seuils pour P50, P95 et coût journalier pour 1 000 utilisateurs actifs. Justifie chaque chiffre.

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Pose la même question simple ("Quelle est la capitale de la France ?") 5 fois de suite.
Note les latences individuelles. Sont-elles identiques ? Explique la variabilité.

**Mes 5 latences :** `___s  ___s  ___s  ___s  ___s`

**Explication :**
```
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Métriques** : Quels KPIs intégreriez-vous dans un tableau de bord de supervision ? Pourquoi le P95 est-il l'indicateur de référence pour les SLA ?
- **Coûts** : Estimez le budget mensuel pour 500 employés faisant chacun 10 questions/jour. Détaillez l'hypothèse de coût par requête.

---

## 💡 Pour aller plus loin

- Compare les TPS entre différents modèles (`gpt-4o` vs `gpt-4o-mini`).
- Mesure le "coût du contexte" : 0 message d'historique vs 8 messages.
- Cherche la définition de P50, P95, P99 dans le vocabulaire SRE.
