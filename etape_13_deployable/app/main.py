"""
Étape 13 — API Chatbot Deployable
Combine : LangChain + RAG optionnel + Prometheus monitoring + JWT security.
Version production-ready.
"""
import os, time, asyncio, logging
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .models import ChatRequest, ChatResponse, HealthResponse, HistoryResponse, TokenResponse
from .database import init_db, save_message, load_history, get_all_sessions
from .llm import get_reply, MODEL
from .metrics import (
    record_request, record_error, update_system_metrics,
    APP_INFO, ACTIVE_SESSIONS, RAG_LATENCY_HISTOGRAM,
    AUTH_ATTEMPTS, INJECTION_BLOCKED
)
from .security import (
    limiter, sanitize, authenticate_user, create_access_token, get_current_user
)
from . import rag as rag_module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERSION = "4.0.0"
STAGE = "13-deployable"

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080"
).split(",")

app = FastAPI(
    title="TP Chatbot API — Deployable",
    description=(
        "Chatbot production-ready : LangChain + RAG + Prometheus + JWT\n\n"
        "**Étape 13** — Version complète combinant toutes les fonctionnalités."
    ),
    version=VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middlewares ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

START_TIME = time.time()


@app.on_event("startup")
async def startup():
    init_db()

    # Initialisation RAG (optionnel)
    rag_available = rag_module.init_rag()

    APP_INFO.info({
        "version": VERSION,
        "model": MODEL,
        "stage": STAGE,
        "rag": str(rag_available),
    })

    # Mise à jour périodique des métriques système
    async def _metrics_loop():
        while True:
            update_system_metrics()
            sessions = get_all_sessions()
            ACTIVE_SESSIONS.set(len(sessions))
            await asyncio.sleep(15)

    asyncio.create_task(_metrics_loop())
    logger.info("Démarrage — modèle: %s | RAG: %s", MODEL, rag_available)


# ── Monitoring endpoints ───────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health():
    """Health check public (pas d'authentification requise)."""
    update_system_metrics()
    return HealthResponse(
        status="ok",
        model=MODEL,
        uptime_seconds=int(time.time() - START_TIME),
        rag_available=rag_module.is_available(),
        version=VERSION,
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Endpoint Prometheus — scraping toutes les 15s."""
    update_system_metrics()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ── Auth ──────────────────────────────────────────────────────────────────

@app.post("/auth/token", response_model=TokenResponse, tags=["Auth"])
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Obtenir un token JWT. Rate limit : 5 tentatives/minute."""
    username = authenticate_user(form_data.username, form_data.password)
    if not username:
        AUTH_ATTEMPTS.labels(status="failure").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    AUTH_ATTEMPTS.labels(status="success").inc()
    token = create_access_token({"sub": username})
    return TokenResponse(access_token=token)


# ── Chat ──────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("10/minute")
async def chat(
    request: Request,
    req: ChatRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Endpoint de chat sécurisé.
    - JWT requis
    - Rate limit : 10 req/min/IP
    - Sanitization + prompt injection guard
    - RAG automatique si disponible (désactivable avec use_rag=false)
    """
    try:
        safe_message = sanitize(req.message)
        safe_session = (
            sanitize(req.session_id) if req.session_id != "default" else req.session_id
        )
    except HTTPException as e:
        if e.status_code == 403:
            INJECTION_BLOCKED.inc()
        raise

    history = load_history(safe_session)
    t0 = time.time()

    # RAG retrieval
    sources = []
    context = ""
    rag_used = False

    if req.use_rag and rag_module.is_available():
        t_rag = time.time()
        docs = rag_module.retrieve(safe_message)
        RAG_LATENCY_HISTOGRAM.observe(time.time() - t_rag)
        if docs:
            context = rag_module.build_context(docs)
            sources = [{"content": d["content"][:200], "source": d["source"]} for d in docs]
            rag_used = True

    try:
        reply, tokens = get_reply(safe_message, history, context=context)
    except Exception as e:
        latency = time.time() - t0
        record_error(type(e).__name__)
        raise HTTPException(status_code=503, detail=f"Erreur LLM : {str(e)}")

    latency = time.time() - t0

    # Estimation tokens input
    tokens_in = int(sum(len(m.content.split()) * 1.3 for m in history)
                    + len(safe_message.split()) * 1.3
                    + len(context.split()) * 1.3)

    record_request(MODEL, "success", latency, tokens_in, tokens, rag=rag_used)

    save_message(safe_session, "user", safe_message)
    save_message(safe_session, "assistant", reply)

    return ChatResponse(
        reply=reply,
        session_id=safe_session,
        latency=round(latency, 3),
        tokens=tokens,
        sources=sources,
        rag_used=rag_used,
    )


@app.get("/history/{session_id}", response_model=HistoryResponse, tags=["Chat"])
async def get_history(session_id: str, current_user: str = Depends(get_current_user)):
    """Historique d'une session (authentification requise)."""
    messages = load_history(session_id, limit=50)
    return HistoryResponse(session_id=session_id, messages=messages, count=len(messages))


@app.get("/sessions", tags=["Admin"])
async def list_sessions(current_user: str = Depends(get_current_user)):
    """Liste de toutes les sessions (authentification requise)."""
    return {"sessions": get_all_sessions(), "user": current_user}
