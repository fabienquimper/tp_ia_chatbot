from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=100)

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
