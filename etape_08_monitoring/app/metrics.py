"""
Étape 08 — Métriques Prometheus
Définition de tous les indicateurs de performance.
"""
import os
import psutil
from prometheus_client import Counter, Histogram, Gauge, Info

# ── Compteurs ──────────────────────────────────────────────────────────────
REQUESTS_TOTAL = Counter(
    "chat_requests_total",
    "Nombre total de requêtes chat",
    ["model", "status"]  # labels: status=success|error
)

TOKENS_TOTAL = Counter(
    "chat_tokens_total",
    "Nombre total de tokens utilisés",
    ["type"]  # labels: type=prompt|completion
)

ERRORS_TOTAL = Counter(
    "chat_errors_total",
    "Nombre total d'erreurs",
    ["error_type"]
)

# ── Histogrammes ────────────────────────────────────────────────────────────
LATENCY_HISTOGRAM = Histogram(
    "chat_latency_seconds",
    "Latence des requêtes chat",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# ── Jauges ──────────────────────────────────────────────────────────────────
MEMORY_USAGE_BYTES = Gauge(
    "process_memory_bytes",
    "Utilisation mémoire du processus Python (RSS)"
)

ACTIVE_SESSIONS = Gauge(
    "chat_active_sessions",
    "Nombre de sessions actives (avec activité dans les 5 dernières minutes)"
)

CONTEXT_SIZE = Gauge(
    "chat_context_messages",
    "Taille moyenne du contexte envoyé au LLM"
)

# ── Info ────────────────────────────────────────────────────────────────────
APP_INFO = Info("chatbot_app", "Informations sur l'application")

def update_system_metrics():
    """Met à jour les métriques système. À appeler périodiquement."""
    process = psutil.Process(os.getpid())
    MEMORY_USAGE_BYTES.set(process.memory_info().rss)

def record_request(model: str, status: str, latency: float, prompt_tokens: int, completion_tokens: int):
    """Enregistre les métriques d'une requête."""
    REQUESTS_TOTAL.labels(model=model, status=status).inc()
    LATENCY_HISTOGRAM.observe(latency)
    TOKENS_TOTAL.labels(type="prompt").inc(prompt_tokens)
    TOKENS_TOTAL.labels(type="completion").inc(completion_tokens)
    update_system_metrics()

def record_error(error_type: str):
    """Enregistre une erreur."""
    ERRORS_TOTAL.labels(error_type=error_type).inc()
