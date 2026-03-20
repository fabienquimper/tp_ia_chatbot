"""
Étape 09 — Client OpenAI
Wrapper autour de l'API OpenAI pour générer des réponses.
"""
import os
from typing import List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from .models import MessageItem

load_dotenv()

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "Tu es un assistant pédagogique spécialisé en intelligence artificielle. "
    "Tu réponds en français, de manière claire et concise."
)


def get_reply(message: str, history: List[MessageItem]) -> Tuple[str, int]:
    """
    Envoie un message au LLM avec l'historique de la conversation.

    Args:
        message: Le message de l'utilisateur.
        history: L'historique des messages précédents.

    Returns:
        Tuple (réponse du LLM, nombre de tokens de complétion).
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for item in history:
        messages.append({"role": item.role, "content": item.content})

    messages.append({"role": "user", "content": message})

    response = _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content or ""
    tokens = response.usage.completion_tokens if response.usage else 0

    return reply, tokens
