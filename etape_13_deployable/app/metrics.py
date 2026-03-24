"""
Étape 13 — Métriques Prometheus
Indicateurs de performance pour le chatbot en production.
"""
import os
import psutil
from prometheus_client import Counter, Histogram, Gauge, Info

# ── Compteurs ──────────────────────────────────────────────────────────────
REQUESTS_TOTAL = Counter(
    "chat_requests_total",
    "Nombre total de requêtes chat",
    ["model", "status", "rag"]   # rag=true|false
)

TOKENS_TOTAL = Counter(
    "chat_tokens_total",
    "Nombre total de tokens utilisés",
    ["type"]  # prompt|completion
)

ERRORS_TOTAL = Counter(
    "chat_errors_total",
    "Nombre total d'erreurs",
    ["error_type"]
)

AUTH_ATTEMPTS = Counter(
    "auth_attempts_total",
    "Tentatives d'authentification",
    ["status"]  # success|failure
)

INJECTION_BLOCKED = Counter(
    "prompt_injection_blocked_total",
    "Tentatives d'injection de prompt bloquées"
)

# ── Histogrammes ────────────────────────────────────────────────────────────
LATENCY_HISTOGRAM = Histogram(
    "chat_latency_seconds",
    "Latence des requêtes chat",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

RAG_LATENCY_HISTOGRAM = Histogram(
    "rag_retrieval_seconds",
    "Latence de la recherche RAG (ChromaDB)",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# ── Jauges ──────────────────────────────────────────────────────────────────
MEMORY_USAGE_BYTES = Gauge(
    "process_memory_bytes",
    "Utilisation mémoire RSS du processus"
)

ACTIVE_SESSIONS = Gauge(
    "chat_active_sessions",
    "Nombre de sessions avec activité"
)

# ── Info ────────────────────────────────────────────────────────────────────
APP_INFO = Info("chatbot_app", "Informations sur l'application")


def update_system_metrics() -> None:
    process = psutil.Process(os.getpid())
    MEMORY_USAGE_BYTES.set(process.memory_info().rss)


def record_request(model: str, status: str, latency: float,
                   prompt_tokens: int, completion_tokens: int, rag: bool = False) -> None:
    REQUESTS_TOTAL.labels(model=model, status=status, rag=str(rag).lower()).inc()
    LATENCY_HISTOGRAM.observe(latency)
    TOKENS_TOTAL.labels(type="prompt").inc(prompt_tokens)
    TOKENS_TOTAL.labels(type="completion").inc(completion_tokens)
    update_system_metrics()


def record_error(error_type: str) -> None:
    ERRORS_TOTAL.labels(error_type=error_type).inc()
