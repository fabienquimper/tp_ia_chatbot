import os
import openai
from dotenv import load_dotenv
from typing import List
from .models import MessageItem

# Dev local : charge depuis etape_00_moteur/.env. En Docker : variables injectées.
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "etape_00_moteur", ".env"))

API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
MODE = os.environ.get("MODE", "cloud")
MODEL = os.environ.get("CLOUD_MODEL", os.environ.get("MODEL", "gpt-4o-mini"))
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "mistral-7b-instruct")
LOCAL_BASE_URL = os.environ.get("LOCAL_BASE_URL", "http://localhost:1234/v1")
MAX_HISTORY = int(os.environ.get("MAX_HISTORY", "8"))

SYSTEM_PROMPT = "Tu es un assistant utile et concis. Réponds en français."

if MODE != "cloud":
    _model = LOCAL_MODEL
    _client = openai.OpenAI(base_url=LOCAL_BASE_URL, api_key="lm-studio")
else:
    _model = MODEL
    _client = openai.OpenAI(api_key=API_KEY)


def get_reply(message: str, history: List[MessageItem]) -> tuple[str, int]:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-MAX_HISTORY:]:
        msgs.append({"role": m.role, "content": m.content})
    msgs.append({"role": "user", "content": message})
    response = _client.chat.completions.create(model=_model, messages=msgs)
    return response.choices[0].message.content, response.usage.completion_tokens
