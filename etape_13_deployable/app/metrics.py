"""
Étape 13 — Métriques Prometheus
Indicateurs de performance pour le chatbot en production.
"""
import os
import logging
import psutil
from prometheus_client import Counter, Histogram, Gauge, Info

logger = logging.getLogger(__name__)

# ── Détection GPU (optionnel — fallback silencieux) ──────────────────────────
try:
    import pynvml as _pynvml
    _pynvml.nvmlInit()
    _GPU_COUNT = _pynvml.nvmlDeviceGetCount()
    _GPU_AVAILABLE = _GPU_COUNT > 0
    _pynvml.nvmlShutdown()
    if _GPU_AVAILABLE:
        logger.info("GPU détecté : %d GPU(s) NVIDIA", _GPU_COUNT)
except Exception:
    _pynvml = None          # type: ignore[assignment]
    _GPU_AVAILABLE = False
    _GPU_COUNT = 0

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

# ── Jauges — Mémoire ────────────────────────────────────────────────────────
MEMORY_USAGE_BYTES = Gauge(
    "process_memory_bytes",
    "Utilisation mémoire RSS du processus"
)

SYSTEM_MEMORY_TOTAL_BYTES = Gauge(
    "system_memory_total_bytes",
    "Mémoire RAM totale du système hôte"
)

SYSTEM_MEMORY_USED_BYTES = Gauge(
    "system_memory_used_bytes",
    "Mémoire RAM utilisée sur le système hôte"
)

# ── Jauges — CPU ────────────────────────────────────────────────────────────
PROCESS_CPU_PERCENT = Gauge(
    "process_cpu_percent",
    "CPU % utilisé par le processus chatbot"
)

SYSTEM_CPU_PERCENT = Gauge(
    "system_cpu_percent",
    "CPU % global du système hôte"
)

# ── Jauges — GPU (seulement renseignées si GPU détecté) ─────────────────────
GPU_UTILIZATION = Gauge(
    "gpu_utilization_percent",
    "Utilisation GPU (%)",
    ["index"]
)

GPU_MEMORY_USED_BYTES = Gauge(
    "gpu_memory_used_bytes",
    "Mémoire VRAM utilisée",
    ["index"]
)

GPU_MEMORY_TOTAL_BYTES = Gauge(
    "gpu_memory_total_bytes",
    "Mémoire VRAM totale",
    ["index"]
)

# ── Jauges — Sessions ────────────────────────────────────────────────────────
ACTIVE_SESSIONS = Gauge(
    "chat_active_sessions",
    "Nombre de sessions avec activité"
)

CONTEXT_SIZE = Gauge(
    "chat_context_messages",
    "Nombre de messages dans l'historique de contexte au moment de la requête"
)

# ── Info ────────────────────────────────────────────────────────────────────
APP_INFO = Info("chatbot_app", "Informations sur l'application")


def update_system_metrics() -> None:
    # Mémoire processus
    process = psutil.Process(os.getpid())
    MEMORY_USAGE_BYTES.set(process.memory_info().rss)

    # Mémoire système
    vm = psutil.virtual_memory()
    SYSTEM_MEMORY_TOTAL_BYTES.set(vm.total)
    SYSTEM_MEMORY_USED_BYTES.set(vm.used)

    # CPU — interval=None : non-bloquant, compare depuis le dernier appel
    PROCESS_CPU_PERCENT.set(process.cpu_percent(interval=None))
    SYSTEM_CPU_PERCENT.set(psutil.cpu_percent(interval=None))

    # GPU — uniquement si NVML disponible et GPU détecté
    if _GPU_AVAILABLE and _pynvml is not None:
        try:
            _pynvml.nvmlInit()
            for i in range(_GPU_COUNT):
                handle = _pynvml.nvmlDeviceGetHandleByIndex(i)
                util = _pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem = _pynvml.nvmlDeviceGetMemoryInfo(handle)
                GPU_UTILIZATION.labels(index=str(i)).set(util.gpu)
                GPU_MEMORY_USED_BYTES.labels(index=str(i)).set(mem.used)
                GPU_MEMORY_TOTAL_BYTES.labels(index=str(i)).set(mem.total)
            _pynvml.nvmlShutdown()
        except Exception:
            pass  # GPU devenu indisponible pendant l'exécution


def record_request(model: str, status: str, latency: float,
                   prompt_tokens: int, completion_tokens: int, rag: bool = False) -> None:
    REQUESTS_TOTAL.labels(model=model, status=status, rag=str(rag).lower()).inc()
    LATENCY_HISTOGRAM.observe(latency)
    TOKENS_TOTAL.labels(type="prompt").inc(prompt_tokens)
    TOKENS_TOTAL.labels(type="completion").inc(completion_tokens)
    update_system_metrics()


def record_error(error_type: str) -> None:
    ERRORS_TOTAL.labels(error_type=error_type).inc()
