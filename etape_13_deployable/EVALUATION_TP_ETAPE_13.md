# 🧠 Évaluation — Étape 13 : Production-Ready (Deployable)

> ⏱ Durée estimée : 90 min | Niveau : Avancé

## 🎯 Enjeu central

C'est la synthèse du projet : toutes les briques précédentes réunies, durcies pour la production.
Le concept central est le **Dockerfile multi-stage** : les tests font partie du build,
et si un test échoue, l'image ne se construit pas.
Pour la première fois, "ça marche sur ma machine" devient "on ne peut pas livrer du code cassé".

```
Stage 1 : builder    → apt + pip (dépendances)
Stage 2 : test       → pytest (exit 1 si échec → build bloqué)
Stage 3 : production → image finale, user non-root, sans outils de build
```

---

## ✅ Checklist de validation

- [ ] J'ai lancé `make dev-bg` et vérifié `make status` (tous services up)
- [ ] J'ai obtenu un token JWT et envoyé une question via `curl` ou Swagger
- [ ] J'ai lancé `make smoke` et lu les résultats
- [ ] J'ai ouvert Grafana et vu des métriques après `make smoke`
- [ ] J'ai lancé `make index-rag-docker` et vérifié `rag_available: true` dans `/health`
- [ ] J'ai lancé `make eval` et noté le score RAG

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Que retourne `make status` ? Quels services sont listés ? Valeur de `rag_available` avant et après `make index-rag-docker` ?

   > _________________________________________________________

2. Après `make smoke`, quel est le score (X/5 PASS) ? Y a-t-il des questions qui échouent ?

   > _________________________________________________________

3. Dans Grafana, après `make eval`, quels panels montrent de l'activité ? Quelle valeur atteint le panel "Tokens consommés" ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. Le Dockerfile a 3 stages : `builder`, `test`, `production`. Que se passe-t-il si un test échoue au stage `test` ? Quel est le comportement de `make dev-bg` ? Pourquoi c'est une garantie importante ?

   > _________________________________________________________

2. L'étape 13 ajoute 5 alertes Prometheus. Quelle est la différence entre une alerte Prometheus et un panel Grafana ? Dans quel cas chacun se déclenche-t-il ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Un développeur propose `make build-skip-tests` pour "gagner du temps" lors d'un déploiement urgent. Dans quels cas (si jamais) est-ce acceptable ? Quelles contre-mesures pour que cette décision laisse une trace ?

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Introduis volontairement un bug dans `app/main.py` (ex : retourne une chaîne vide dans une condition).
Tente `make dev-bg`. Que se passe-t-il ? Corrige le bug et relance.

**Erreur observée :**
```
_____________________________________________________________
```
**Comportement du build avec le bug :**
```
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **CI/CD** : Comment le Dockerfile multi-stage (`builder → test → production`) simule-t-il un pipeline CI/CD local ? Quelles étapes d'un vrai pipeline GitHub Actions cela reproduit-il ?
- **Monitoring** : À partir des alertes Prometheus de cette étape, rédigez un plan d'escalade d'incident : qui est alerté pour `ChatbotDown` (critical) vs `HighLatency` (warning) ? Quel délai de réponse ?
- **Sécurité** : `make test-security` lance `bandit`. Quelles catégories de vulnérabilités détecte-t-il ? Donnez 2 exemples de failles qu'il trouverait dans du code Python typique.

---

## 💡 Pour aller plus loin

- Lance `make prod` (Nginx + TLS) et compare l'architecture avec `make dev-bg` : quelles couches Nginx ajoute-t-il ?
- Dans `prometheus-alerts.yml`, modifie le seuil de `HighMemoryUsage` à 200 MB et observe si l'alerte se déclenche.
- Explore `make eval-verbose` : lis les réponses complètes pour les questions qui échouent.
