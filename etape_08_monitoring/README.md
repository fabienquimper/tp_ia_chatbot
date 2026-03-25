# Étape 08 — Prometheus & Grafana

## Objectif
Instrumenter le chatbot avec des métriques Prometheus et visualiser dans Grafana.

## Architecture
```
FastAPI → /metrics → Prometheus (scrape 15s) → Grafana (dashboard)
```

## Métriques exposées
| Métrique | Type | Description |
|----------|------|-------------|
| `chat_requests_total` | Counter | Nb requêtes par modèle/status |
| `chat_latency_seconds` | Histogram | Distribution latence |
| `chat_tokens_total` | Counter | Tokens prompt/completion |
| `chat_errors_total` | Counter | Erreurs par type d'exception |
| `chat_context_messages` | Gauge | Taille de l'historique à chaque requête |
| `chat_active_sessions` | Gauge | Sessions actives |
| `process_memory_bytes` | Gauge | RAM RSS du processus Python |
| `system_memory_total_bytes` | Gauge | RAM totale du système hôte |
| `system_memory_used_bytes` | Gauge | RAM utilisée sur le système hôte |
| `process_cpu_percent` | Gauge | CPU % du processus chatbot |
| `system_cpu_percent` | Gauge | CPU % global du système |

## Lancement
```bash
cp .env.example .env
docker-compose up --build -d
```

## Accès
- API : http://localhost:8000/docs
- Métriques raw : http://localhost:8000/metrics
- Prometheus : http://localhost:9090
- Grafana : http://localhost:3000 (admin / admin123)

## Générer du trafic
```bash
pip install httpx
python send_test_requests.py http://localhost:8000 50
```

## Requêtes PromQL utiles
```promql
# Latence P95
histogram_quantile(0.95, rate(chat_latency_seconds_bucket[5m]))

# Requêtes par seconde
rate(chat_requests_total[1m])

# Mémoire en MB
process_memory_bytes / 1024 / 1024
```

## Exercice
1. Lancez la stack : `docker-compose up --build -d`
2. Envoyez 50 requêtes : `python send_test_requests.py`
3. Ouvrez Prometheus : vérifiez que les métriques sont scraped
4. Ouvrez Grafana : créez un dashboard avec latence P95 et RPS
5. Bonus : ajoutez une alerte si latence P95 > 5s


# Grafana exemple

![alt text](image.png)
![alt text](image-1.png)

# Medric output

Exemple http://localhost:8000/metrics
```
# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 2508.0
python_gc_objects_collected_total{generation="1"} 464.0
python_gc_objects_collected_total{generation="2"} 0.0
# HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 253.0
python_gc_collections_total{generation="1"} 22.0
python_gc_collections_total{generation="2"} 2.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="11",patchlevel="15",version="3.11.15"} 1.0
# HELP process_virtual_memory_bytes Virtual memory size in bytes.
# TYPE process_virtual_memory_bytes gauge
process_virtual_memory_bytes 1.97021696e+08
# HELP process_resident_memory_bytes Resident memory size in bytes.
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 8.6351872e+07
# HELP process_start_time_seconds Start time of the process since unix epoch in seconds.
# TYPE process_start_time_seconds gauge
process_start_time_seconds 1.77428245565e+09
# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 4.01
# HELP process_open_fds Number of open file descriptors.
# TYPE process_open_fds gauge
process_open_fds 60.0
# HELP process_max_fds Maximum number of open file descriptors.
# TYPE process_max_fds gauge
process_max_fds 1.048576e+06
# HELP chat_requests_total Nombre total de requêtes chat
# TYPE chat_requests_total counter
chat_requests_total{model="gpt-4o-mini",status="success"} 20.0
# HELP chat_requests_created Nombre total de requêtes chat
# TYPE chat_requests_created gauge
chat_requests_created{model="gpt-4o-mini",status="success"} 1.7742825063502681e+09
# HELP chat_tokens_total Nombre total de tokens utilisés
# TYPE chat_tokens_total counter
chat_tokens_total{type="prompt"} 16300.0
chat_tokens_total{type="completion"} 10853.0
# HELP chat_tokens_created Nombre total de tokens utilisés
# TYPE chat_tokens_created gauge
chat_tokens_created{type="prompt"} 1.7742825063503132e+09
chat_tokens_created{type="completion"} 1.7742825063503366e+09
# HELP chat_errors_total Nombre total d'erreurs
# TYPE chat_errors_total counter
# HELP chat_latency_seconds Latence des requêtes chat
# TYPE chat_latency_seconds histogram
chat_latency_seconds_bucket{le="0.1"} 0.0
chat_latency_seconds_bucket{le="0.25"} 0.0
chat_latency_seconds_bucket{le="0.5"} 0.0
chat_latency_seconds_bucket{le="1.0"} 0.0
chat_latency_seconds_bucket{le="2.0"} 0.0
chat_latency_seconds_bucket{le="5.0"} 2.0
chat_latency_seconds_bucket{le="10.0"} 3.0
chat_latency_seconds_bucket{le="30.0"} 11.0
chat_latency_seconds_bucket{le="+Inf"} 20.0
chat_latency_seconds_count 20.0
chat_latency_seconds_sum 580.8747315406799
# HELP chat_latency_seconds_created Latence des requêtes chat
# TYPE chat_latency_seconds_created gauge
chat_latency_seconds_created 1.7742824575659895e+09
# HELP process_memory_bytes Utilisation mémoire du processus Python (RSS)
# TYPE process_memory_bytes gauge
process_memory_bytes 8.6351872e+07
# HELP chat_active_sessions Nombre de sessions actives (avec activité dans les 5 dernières minutes)
# TYPE chat_active_sessions gauge
chat_active_sessions 5.0
# HELP chat_context_messages Taille moyenne du contexte envoyé au LLM
# TYPE chat_context_messages gauge
chat_context_messages 0.0
# HELP chatbot_app_info Informations sur l'application
# TYPE chatbot_app_info gauge
chatbot_app_info{model="gpt-4o-mini",stage="08-monitoring",version="2.0.0"} 1.0
```

Commentaire:
Ce sont les métriques exposées par l'app FastAPI (endpoint /metrics), pas Prometheus lui-même. C'est ce que Prometheus vient scraper toutes les 15s.

Il y en a deux catégories :

Métriques Python auto-générées par la lib prometheus_client :

python_gc_* — garbage collector Python (objets collectés/non collectables)
python_info — version Python (3.11.15 CPython)
process_* — mémoire virtuelle/RSS, CPU, file descriptors, uptime
Vos métriques métier définies dans metrics.py :

chat_requests_total — 20 requêtes success avec label model="gpt-4o-mini"
chat_tokens_total — 16 300 tokens prompt / 10 853 completion
chat_latency_seconds — histogramme : toutes les requêtes sont entre 5s et +Inf (modèle lent)
chat_active_sessions — 5 sessions actives
chat_errors_total — vide (aucune erreur)
chat_context_messages — taille de l'historique au moment de la requête
chatbot_app_info — métadonnées de l'app
Prometheus stocke tout ça dans sa TSDB (time series database) et Grafana lit ensuite via PromQL.