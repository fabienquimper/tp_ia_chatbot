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

SYSTEM_MEMORY_TOTAL_BYTES = Gauge(
    "system_memory_total_bytes",
    "Mémoire RAM totale du système hôte"
)

SYSTEM_MEMORY_USED_BYTES = Gauge(
    "system_memory_used_bytes",
    "Mémoire RAM utilisée sur le système hôte"
)

PROCESS_CPU_PERCENT = Gauge(
    "process_cpu_percent",
    "CPU % utilisé par le processus chatbot"
)

SYSTEM_CPU_PERCENT = Gauge(
    "system_cpu_percent",
    "CPU % global du système hôte"
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
    vm = psutil.virtual_memory()
    SYSTEM_MEMORY_TOTAL_BYTES.set(vm.total)
    SYSTEM_MEMORY_USED_BYTES.set(vm.used)
    # interval=None : non-bloquant, compare depuis le dernier appel
    PROCESS_CPU_PERCENT.set(process.cpu_percent(interval=None))
    SYSTEM_CPU_PERCENT.set(psutil.cpu_percent(interval=None))

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
