import os
import openai
from typing import List
from .models import MessageItem

API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_HISTORY = int(os.environ.get("MAX_HISTORY", "8"))

SYSTEM_PROMPT = "Tu es un assistant utile et concis. Réponds en français."

def get_client() -> openai.OpenAI:
    return openai.OpenAI(api_key=API_KEY)

def get_reply(message: str, history: List[MessageItem]) -> tuple[str, int]:
    client = get_client()
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-MAX_HISTORY:]:
        msgs.append({"role": m.role, "content": m.content})
    msgs.append({"role": "user", "content": message})
    response = client.chat.completions.create(model=MODEL, messages=msgs)
    return response.choices[0].message.content, response.usage.completion_tokens
