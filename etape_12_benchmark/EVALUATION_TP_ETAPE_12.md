# 🧠 Évaluation — Étape 12 : Benchmark LLM-as-Judge

> ⏱ Durée estimée : 60 min | Niveau : Avancé

## 🎯 Enjeu central

Choisir un modèle LLM sans benchmark, c'est acheter une voiture sans l'essayer.
Cette étape introduit l'évaluation **objective et reproductible** : un jeu de questions standardisé
(`eval_set.jsonl`), une notation par un autre LLM (LLM-as-Judge), et une analyse qualité/prix.
L'enjeu : justifier un choix technique avec des données.

```
eval_set.jsonl → benchmark.py → LLM 1, LLM 2… → judge.py → résultats
```

---

## ✅ Checklist de validation

- [ ] J'ai lancé `python benchmark.py` pour au moins 1 modèle
- [ ] J'ai lancé `python analyse.py` et lu le tableau comparatif
- [ ] J'ai compris comment `judge.py` note les réponses (score 1-10)
- [ ] J'ai inspecté `eval_set.jsonl` et compris la structure
- [ ] J'ai ajouté au moins 2 questions dans `eval_set.jsonl` et relancé

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Pour les modèles benchmarkés : score LLM-as-Judge, latence moyenne, coût total pour les 20 questions. Présente un mini-tableau.

   | Modèle | Score | Latence | Coût |
   |--------|-------|---------|------|
   | _______ | ___/10 | ___s | $___ |
   | _______ | ___/10 | ___s | $___ |

2. Quel modèle a le P95 de latence le plus élevé ? Est-ce le même qui a le meilleur score ?

   > _________________________________________________________

3. Dans `eval_set.jsonl`, quelle est la structure d'une question ? Donne un exemple avec ses `expected_keywords`.

   > _________________________________________________________

### Niveau 2 — Analyse
1. Le LLM-as-Judge utilise un LLM pour noter les réponses d'autres LLMs. Quels **biais** cette méthode peut-elle introduire ? (Quel LLM est juge ? Favorise-t-il ses "frères" ?)

   > _________________________________________________________

2. Si les questions de `eval_set.jsonl` sont mal choisies (trop faciles, biaisées), qu'est-ce que ça change pour la validité des résultats ? Comment construire un bon jeu d'évaluation ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Tu dois recommander un modèle LLM pour un chatbot de support technique avec un budget de 500€/mois pour 50 000 requêtes. Quel modèle recommandes-tu ? Montre le calcul de coût.

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Ajoute 3 questions dans `eval_set.jsonl` sur un domaine que tu connais bien.
Relance `benchmark.py`. Les scores sont-ils cohérents avec ta propre évaluation "humaine" ?
Où le LLM-as-Judge est-il le plus en désaccord avec toi ?

**Questions ajoutées :** `__________________________________`

**Désaccord observé :**
```
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Choix techniques** : Comment justifiez-vous le choix de votre modèle LLM dans le dossier E8 ? Quelles métriques (score, coût, latence) utilisez-vous, et comment les reliez-vous aux besoins métier ?
- **Reproductibilité** : Comment garantir que le benchmark reste comparable dans le temps si le modèle est mis à jour par le fournisseur ? Proposez une stratégie de versioning de l'évaluation.

---

## 💡 Pour aller plus loin

- Modifie le prompt de `judge.py` pour noter sur d'autres critères (exactitude factuelle, ton, longueur) : les scores changent-ils ?
- Cherche des benchmarks publics (MMLU, HumanEval) : comment se comparent `gpt-4o-mini` et `gpt-4o` ?
- Explore la notion de **"benchmark contamination"** : pourquoi certains benchmarks publics ne sont plus fiables ?
