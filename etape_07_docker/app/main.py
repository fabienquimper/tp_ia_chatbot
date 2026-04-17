"""
Étape 07 — FastAPI Chatbot API
Endpoints: GET /health, POST /chat, GET /history/{session_id}
"""
import os, time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ChatRequest, ChatResponse, HealthResponse, HistoryResponse
from .database import init_db, save_message, load_history, get_all_sessions
from .llm import get_reply, MODEL

START_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie — remplace @app.on_event('startup')."""
    init_db()
    yield

app = FastAPI(
    title="TP Chatbot API",
    description="Assistant IA — Du Script au Système (Étape 07)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod : restreindre aux domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health():
    """Point de contrôle de santé — indispensable en production."""
    return HealthResponse(
        status="ok",
        model=MODEL,
        uptime_seconds=int(time.time() - START_TIME)
    )

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(req: ChatRequest):
    """Envoie un message et reçoit une réponse du LLM."""
    history = load_history(req.session_id)
    t0 = time.time()
    try:
        reply, tokens = get_reply(req.message, history)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur LLM : {str(e)}")
    latency = time.time() - t0

    save_message(req.session_id, "user", req.message)
    save_message(req.session_id, "assistant", reply)

    return ChatResponse(
        reply=reply,
        session_id=req.session_id,
        latency=round(latency, 3),
        tokens=tokens
    )

@app.get("/history/{session_id}", response_model=HistoryResponse, tags=["Chat"])
async def get_history(session_id: str):
    """Récupère l'historique d'une session."""
    messages = load_history(session_id, limit=50)
    return HistoryResponse(
        session_id=session_id,
        messages=messages,
        count=len(messages)
    )

@app.get("/sessions", tags=["Admin"])
async def list_sessions():
    """Liste toutes les sessions actives."""
    return {"sessions": get_all_sessions()}
