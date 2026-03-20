import os
import openai
from typing import List
from .models import MessageItem

API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MAX_HISTORY = int(os.environ.get("MAX_HISTORY", "8"))
MODE = os.environ.get("MODE", "cloud")
LM_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")

SYSTEM_PROMPT = "Tu es un assistant utile et concis. Réponds en français."

def get_client() -> openai.OpenAI:
    if MODE == "local":
        return openai.OpenAI(base_url=LM_URL, api_key="lm-studio")
    return openai.OpenAI(api_key=API_KEY)

def get_reply(message: str, history: List[MessageItem]) -> tuple[str, int]:
    """Envoie un message au LLM et retourne (réponse, nb_tokens)."""
    client = get_client()

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Fenêtre glissante
    for m in history[-MAX_HISTORY:]:
        msgs.append({"role": m.role, "content": m.content})
    msgs.append({"role": "user", "content": message})

    response = client.chat.completions.create(model=MODEL, messages=msgs)
    reply = response.choices[0].message.content
    tokens = response.usage.completion_tokens
    return reply, tokens
