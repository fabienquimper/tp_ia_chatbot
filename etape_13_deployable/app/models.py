"""
Étape 13 — Modèles Pydantic
Schémas de validation pour l'API complète (sécurité + monitoring + RAG).
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=100)
    use_rag: bool = Field(default=True, description="Activer la recherche RAG")


class MessageItem(BaseModel):
    role: str
    content: str


class SourceDocument(BaseModel):
    content: str
    source: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    latency: float
    tokens: int
    sources: List[SourceDocument] = Field(default_factory=list)
    rag_used: bool = False


class HealthResponse(BaseModel):
    status: str
    model: str
    llm_url: str
    llm_reachable: bool
    uptime_seconds: int
    rag_available: bool = False
    version: str = "4.0.0"


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[MessageItem]
    count: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str
