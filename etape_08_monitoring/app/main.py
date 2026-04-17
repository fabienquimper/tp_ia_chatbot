"""
Étape 08 — FastAPI + Prometheus Monitoring
Ajoute l'instrumentation complète avec métriques Prometheus.
"""
import os, time, asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .models import ChatRequest, ChatResponse, HealthResponse, HistoryResponse
from .database import init_db, save_message, load_history, get_all_sessions
from .llm import get_reply, MODEL
from .metrics import (
    record_request, record_error, update_system_metrics,
    APP_INFO, ACTIVE_SESSIONS, CONTEXT_SIZE
)

START_TIME = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie — remplace @app.on_event('startup')."""
    init_db()
    APP_INFO.info({
        "version": "2.0.0",
        "model": MODEL,
        "stage": "08-monitoring"
    })
    # Mise à jour périodique des métriques système
    async def update_loop():
        while True:
            update_system_metrics()
            sessions = get_all_sessions()
            ACTIVE_SESSIONS.set(len(sessions))
            await asyncio.sleep(15)
    asyncio.create_task(update_loop())
    yield

app = FastAPI(
    title="TP Chatbot API — Monitoring",
    description="Chatbot avec métriques Prometheus (Étape 08)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health():
    update_system_metrics()
    return HealthResponse(
        status="ok",
        model=MODEL,
        uptime_seconds=int(time.time() - START_TIME)
    )

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Endpoint Prometheus — scraped toutes les 15s."""
    update_system_metrics()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(req: ChatRequest):
    history = load_history(req.session_id)
    CONTEXT_SIZE.set(len(history))
    t0 = time.time()

    try:
        reply, tokens_out, tokens_in = get_reply(req.message, history)
        latency = time.time() - t0

        record_request(MODEL, "success", latency, tokens_in, tokens_out)

    except Exception as e:
        latency = time.time() - t0
        record_error(type(e).__name__)
        record_request(MODEL, "error", latency, 0, 0)
        raise HTTPException(status_code=503, detail=f"Erreur LLM : {str(e)}")

    save_message(req.session_id, "user", req.message)
    save_message(req.session_id, "assistant", reply)

    return ChatResponse(
        reply=reply,
        session_id=req.session_id,
        latency=round(latency, 3),
        tokens=tokens_out
    )

@app.get("/history/{session_id}", response_model=HistoryResponse, tags=["Chat"])
async def get_history(session_id: str):
    messages = load_history(session_id, limit=50)
    return HistoryResponse(
        session_id=session_id,
        messages=messages,
        count=len(messages)
    )

@app.get("/sessions", tags=["Admin"])
async def list_sessions():
    return {"sessions": get_all_sessions()}
