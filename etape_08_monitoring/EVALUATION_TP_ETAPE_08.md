# 🧠 Évaluation — Étape 08 : Prometheus & Grafana

> ⏱ Durée estimée : 60 min | Niveau : Intermédiaire

## 🎯 Enjeu central

Tu ne peux pas corriger ce que tu ne vois pas. Cette étape instrumente l'API avec des métriques
Prometheus et les visualise dans Grafana. L'enjeu : distinguer les métriques **techniques**
(RAM, CPU) des métriques **métier** (tokens, erreurs), et comprendre comment Prometheus
agrège les données dans le temps via PromQL.

---

## ✅ Checklist de validation

- [ ] J'ai lancé la stack (`docker-compose up -d`) et accédé à Grafana (`:3000`)
- [ ] J'ai envoyé 50 requêtes avec `python send_test_requests.py`
- [ ] J'ai lu les métriques brutes sur `http://localhost:8000/metrics`
- [ ] J'ai exécuté une requête PromQL dans Prometheus (`:9090`)
- [ ] J'ai observé un panel Grafana avec la latence P95

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Sur `/metrics`, quelle valeur affiche `chat_requests_total` après tes 50 requêtes ? Quel label distingue succès et erreurs ?

   > _________________________________________________________

2. Dans Prometheus, tape `histogram_quantile(0.95, rate(chat_latency_seconds_bucket[5m]))`. Quelle valeur obtiens-tu ?

   > _________________________________________________________

3. Quelle est la valeur de `process_memory_bytes` en MB ? Et `chat_active_sessions` ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. Prometheus **scrape** (tire) les métriques toutes les 15s. Pourquoi cette architecture "pull" est-elle préférable au "push" (l'app envoie elle-même) dans un environnement cloud avec des services qui scalent dynamiquement ?

   > _________________________________________________________

2. Quelle est la différence entre un **Counter** et un **Gauge** ? Donne un exemple de chaque dans le code et explique pourquoi on ne peut pas utiliser un Gauge pour `chat_requests_total`.

   > _________________________________________________________

### Niveau 3 — Décision
1. Tu es d'astreinte, une alerte sonne à 3h du matin. Quelles métriques regardes-tu en premier et dans quel ordre pour diagnostiquer en moins de 5 minutes ? Décris ton workflow de debug.

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Arrête le conteneur `chatbot` (`docker compose stop chatbot`).
Observe dans Grafana ce qui se passe pendant 2-3 minutes.
Que montrent les graphiques quand le service est down ?

**Ce que j'ai observé dans Grafana :**
```
_____________________________________________________________
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Monitoring** : Définissez les alertes Prometheus pour ce chatbot en production. Quels seuils pour le taux d'erreur, la latence P95, et la consommation mémoire ? Justifiez chaque seuil.
- **Prévention des risques** : Comment le monitoring Prometheus/Grafana s'intègre dans une démarche de prévention des incidents (plutôt que de réaction) ? Donnez un exemple concret.

---

## 💡 Pour aller plus loin

- Crée une alerte Grafana si `chat_latency_seconds` P95 dépasse 5s.
- Explore la différence entre `rate()` et `irate()` en PromQL.
- Cherche ce qu'est un **SLO** (Service Level Objective) et définis-en un pour ce chatbot.
