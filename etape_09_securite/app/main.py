"""
Étape 09 — API Sécurisée
Rate limiting, prompt guard, JWT authentication, CORS restrictif.
"""
import os, time
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .models import ChatRequest, ChatResponse, HealthResponse, HistoryResponse, TokenResponse, LoginRequest
from .database import init_db, save_message, load_history
from .llm import get_reply, MODEL
from .security import (
    limiter, sanitize, authenticate_user, create_access_token, get_current_user
)

# Origines autorisées (CORS)
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080"
).split(",")

app = FastAPI(
    title="TP Chatbot API — Sécurisée",
    description="Chatbot avec rate limiting, prompt guard et JWT (Étape 09)",
    version="3.0.0"
)

# ── Rate Limiter ──────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS restrictif ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Jamais ["*"] en production !
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

START_TIME = time.time()

@app.on_event("startup")
async def startup():
    init_db()

# ── Auth endpoints ────────────────────────────────────────────────────────

@app.post("/auth/token", response_model=TokenResponse, tags=["Auth"])
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """Obtenir un token JWT. Rate limit : 5 tentatives/minute."""
    username = authenticate_user(form_data.username, form_data.password)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": username})
    return TokenResponse(access_token=token)

# ── Health ────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health():
    """Health check public (pas besoin d'authentification)."""
    return HealthResponse(
        status="ok",
        model=MODEL,
        uptime_seconds=int(time.time() - START_TIME)
    )

# ── Chat ──────────────────────────────────────────────────────────────────

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
@limiter.limit("10/minute")
async def chat(
    request: Request,
    req: ChatRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Endpoint de chat sécurisé.
    - Authentification JWT requise
    - Rate limit : 10 req/minute/IP
    - Sanitization + prompt injection guard
    """
    # Sanitization et prompt guard
    safe_message = sanitize(req.message)
    safe_session = sanitize(req.session_id) if req.session_id != "default" else req.session_id

    history = load_history(safe_session)
    t0 = time.time()

    try:
        reply, tokens = get_reply(safe_message, history)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur LLM : {str(e)}")

    latency = time.time() - t0
    save_message(safe_session, "user", safe_message)
    save_message(safe_session, "assistant", reply)

    return ChatResponse(
        reply=reply,
        session_id=safe_session,
        latency=round(latency, 3),
        tokens=tokens
    )

@app.get("/history/{session_id}", response_model=HistoryResponse, tags=["Chat"])
async def get_history(session_id: str, current_user: str = Depends(get_current_user)):
    """Historique d'une session (authentification requise)."""
    messages = load_history(session_id, limit=50)
    return HistoryResponse(session_id=session_id, messages=messages, count=len(messages))
