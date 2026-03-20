import os, time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ChatRequest, ChatResponse, HealthResponse, HistoryResponse
from .database import init_db, save_message, load_history
from .llm import get_reply, MODEL

app = FastAPI(title="TP Chatbot — Tests", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

START_TIME = time.time()

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", model=MODEL, uptime_seconds=int(time.time() - START_TIME))

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history = load_history(req.session_id)
    t0 = time.time()
    try:
        reply, tokens = get_reply(req.message, history)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
    latency = time.time() - t0
    save_message(req.session_id, "user", req.message)
    save_message(req.session_id, "assistant", reply)
    return ChatResponse(reply=reply, session_id=req.session_id, latency=round(latency, 3), tokens=tokens)

@app.get("/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str):
    messages = load_history(session_id, limit=50)
    return HistoryResponse(session_id=session_id, messages=messages, count=len(messages))
