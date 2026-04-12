# 🧠 Évaluation — Étape 10 : Test de Charge (Locust)

> ⏱ Durée estimée : 60 min | Niveau : Avancé

## 🎯 Enjeu central

Une app qui marche pour 1 utilisateur peut exploser pour 50. Les tests de charge
révèlent les limites **avant** que les vrais utilisateurs les atteignent.
L'enjeu : identifier le goulot d'étranglement (API ? LLM ? DB ?) et
comprendre ce que signifie un SLA réaliste.

| KPI cible | Seuil |
|-----------|-------|
| Taux d'échec | < 1% |
| Latence P50 | < 2s |
| Latence P95 | < 5s |
| RPS | > 20 |

---

## ✅ Checklist de validation

- [ ] J'ai lancé le test `small` (20 users, 2 min) et obtenu des résultats
- [ ] J'ai noté le P95, le taux d'échec et le RPS
- [ ] J'ai lancé le test `medium` (50 users) et comparé les résultats
- [ ] J'ai analysé les résultats avec `python analyse_results.py`
- [ ] J'ai identifié à quel palier le taux d'échec dépasse 1%

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Pour le test `small` (20 users) : tes chiffres de P50, P95 et taux d'échec. Dans les SLA cibles ?

   > P50 : ___s | P95 : ___s | Taux d'échec : ___%

2. En passant de 20 à 50 users, quelle métrique se dégrade le plus vite ? Quel facteur d'aggravation observes-tu ?

   > _________________________________________________________

3. Pendant le test, quelle est la consommation CPU et mémoire du conteneur (`docker stats`) ?

   > CPU : ___% | RAM : ___ MB

### Niveau 2 — Analyse
1. Dans `locustfile.py`, quelle logique définit le comportement de chaque utilisateur virtuel ? Comment Locust simule-t-il le "think time" (pause entre requêtes) d'un vrai utilisateur ?

   > _________________________________________________________

2. Le goulot d'étranglement est presque toujours le **LLM**, pas l'API FastAPI. Explique pourquoi — et que se passerait-il avec 5 instances de l'API en parallèle ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Le chatbot doit supporter 500 users simultanés. À partir de tes résultats, combien d'instances seraient nécessaires ? Quel coût infrastructure ? Présente le raisonnement.

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Lance Locust en mode UI (`locust -f locustfile.py --host=http://localhost:8000`),
ouvre `http://localhost:8089`, et augmente progressivement de 1 à 50 users (spawn rate : 1/s).
À quel seuil la latence commence-t-elle à décrocher ?

**Seuil de décrochage :** `_____ users simultanés`

**P95 à ce seuil :** `_____ secondes`

---

## 📋 Lien avec le dossier E8

- **Tests** : Comment intégreriez-vous les tests de charge dans un pipeline CI/CD ? À quelle fréquence, et quels seuils bloqueraient la mise en production ?
- **Prévention des risques** : Identifiez le scénario de dégradation le plus probable en production et proposez une stratégie d'atténuation (autoscaling, cache, queue).

---

## 💡 Pour aller plus loin

- Ajoute un scénario dans `locustfile.py` qui teste aussi `GET /history/{session_id}` : est-il plus rapide que `POST /chat` ?
- Compare les résultats avec et sans RAG activé : le RAG ajoute-t-il de la latence significative ?
- Cherche la différence entre load test, stress test et spike test.
