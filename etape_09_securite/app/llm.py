"""
Étape 09 — Client OpenAI
Wrapper autour de l'API OpenAI pour générer des réponses.
"""
import os
from typing import List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
from .models import MessageItem

# Dev local : charge depuis etape_00_moteur/.env. En Docker : variables injectées.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "etape_00_moteur", ".env"))

MODE = os.environ.get("MODE", "cloud")
MODEL = os.environ.get("CLOUD_MODEL", os.environ.get("MODEL", "gpt-4o-mini"))
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "mistral-7b-instruct")
LOCAL_BASE_URL = os.environ.get("LOCAL_BASE_URL", "http://localhost:1234/v1")

if MODE == "local":
    _model = LOCAL_MODEL
    _client = OpenAI(base_url=LOCAL_BASE_URL, api_key="lm-studio")
else:
    _model = MODEL
    _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

MODEL = _model  # modèle effectivement utilisé (local ou cloud)

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
        model=_model,
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content or ""
    tokens = response.usage.completion_tokens if response.usage else 0
    return reply, tokens
