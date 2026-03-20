from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="Message de l'utilisateur")
    session_id: str = Field(default="default", description="Identifiant de session")

class MessageItem(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    latency: float
    tokens: int

class HealthResponse(BaseModel):
    status: str
    model: str
    uptime_seconds: int
    version: str = "1.0.0"

class HistoryResponse(BaseModel):
    session_id: str
    messages: List[MessageItem]
    count: int
