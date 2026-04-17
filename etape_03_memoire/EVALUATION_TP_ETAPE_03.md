# 🧠 Évaluation — Étape 03 : La Mémoire Tampon

> ⏱ Durée estimée : 45 min | Niveau : Intermédiaire

## 🎯 Enjeu central

Le contexte d'un LLM est une ressource limitée **et payante**. Garder tout l'historique
indéfiniment est impraticable : ça coûte de plus en plus cher et ralentit les réponses.
Deux stratégies s'affrontent : fenêtre glissante (simple, prévisible) vs résumé automatique
(plus coûteux, mais préserve l'essentiel).

---

## ✅ Checklist de validation

- [ ] J'ai lancé `01_memory_window.py` avec `MAX_HISTORY=4`
- [ ] J'ai posé 10 questions sur des sujets différents et tapé `fenetre`
- [ ] J'ai vérifié que les premières questions avaient disparu de la fenêtre
- [ ] J'ai lancé `02_memory_summary.py` et comparé ce qu'il retient
- [ ] J'ai changé `MAX_HISTORY` à 2 et observé l'effet sur la cohérence

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Avec `MAX_HISTORY=4`, quel est le 1er message qui disparaît après le 3e échange ? Qu'est-ce qui le remplace ?

   > _________________________________________________________

2. Dans `memory_summary.py`, que contient le résumé généré après avoir dépassé la limite ? Reproduis un extrait.

   > _________________________________________________________

3. Avec `MAX_HISTORY=2`, si tu donnes ton prénom au 1er échange et poses une question au 3e, le bot se souvient-il de toi ? Pourquoi ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. La fenêtre glissante coupe les premiers messages. Pourquoi c'est problématique si le `system prompt` contient des instructions importantes que l'utilisateur ne voit pas ?

   > _________________________________________________________

2. Le résumé automatique fait **2 appels LLM** au lieu d'1. Dans quel cas est-ce justifié ? Dans quel cas est-ce une mauvaise idée ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Tu déploies un chatbot de support client (conversations de ~15 échanges en moyenne). Fenêtre glissante (`MAX_HISTORY=8`) ou résumé automatique ? Argumente : coût, fiabilité, expérience utilisateur.

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Lance `memory_window.py` avec `MAX_HISTORY=20`. Conduis 25 échanges.
Mesure la latence à l'échange 1 vs l'échange 25. Quelle tendance observes-tu ?

**Latence échange 1 :** `___s` | **Latence échange 25 :** `___s`

**Explication :**
```
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Architecture** : Quel mécanisme de gestion de la mémoire choisiriez-vous pour un assistant RH devant se souvenir du contexte d'un entretien de plusieurs heures ? Justifiez le choix technique.
- **Coûts** : Calculez l'impact d'une fenêtre de 20 messages vs 4 messages sur le coût mensuel pour 1 000 utilisateurs / 10 échanges par jour. Formulez une recommandation.

---

## 💡 Pour aller plus loin

- Essaie `MAX_HISTORY=0` : le bot est-il encore utilisable ?
- Modifie le prompt de résumé dans `memory_summary.py` pour qu'il soit limité à 50 mots.
- Cherche les tailles de context window : GPT-4o (128K), Mistral 7B (~8K). Qu'est-ce que ça change pour la stratégie ?
