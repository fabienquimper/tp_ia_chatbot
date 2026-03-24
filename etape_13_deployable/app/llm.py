"""
Étape 13 — LLM via LangChain
Orchestration LangChain avec support RAG optionnel.
Supporte mode cloud (OpenAI) et mode local (LM Studio / Ollama).
"""
import os
import re
import logging
from typing import List, Tuple

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

from .models import MessageItem

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "etape_00_moteur", ".env"),
            override=False)

logger = logging.getLogger(__name__)

MODE = os.environ.get("MODE", "cloud")
MODEL = os.environ.get("MODEL", "gpt-4o-mini")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "mistral-7b-instruct")
LOCAL_BASE_URL = os.environ.get("LOCAL_BASE_URL", "http://host.docker.internal:1234/v1")

# ── Initialisation LLM ─────────────────────────────────────────────────────
if MODE == "local":
    _active_model = LOCAL_MODEL
    llm = ChatOpenAI(
        model=LOCAL_MODEL,
        base_url=LOCAL_BASE_URL,
        api_key="lm-studio",
        temperature=0.7,
    )
else:
    _active_model = MODEL
    llm = ChatOpenAI(
        model=MODEL,
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        temperature=0.7,
    )

MODEL = _active_model  # export du modèle effectif

# ── Prompts ────────────────────────────────────────────────────────────────
_SYSTEM_BASE = (
    "Tu es un assistant pédagogique spécialisé en intelligence artificielle. "
    "Tu réponds en français, de manière claire et concise. "
    "Si on te pose une question sur un contexte documentaire, appuie-toi dessus en priorité."
)

_SYSTEM_RAG = (
    "Tu es un assistant virtuel expert. Réponds UNIQUEMENT en te basant sur le contexte fourni. "
    "Si la réponse n'est pas dans le contexte, dis 'Je n'ai pas cette information dans ma base documentaire.' "
    "Réponds en français, de façon concise et professionnelle.\n\nContexte :\n{context}"
)

_prompt_plain = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_BASE),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

_prompt_rag = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM_RAG),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

_chain_plain = _prompt_plain | llm | StrOutputParser()
_chain_rag   = _prompt_rag   | llm | StrOutputParser()


def _to_lc_messages(history: List[MessageItem]):
    """Convertit l'historique DB en messages LangChain."""
    msgs = []
    for item in history:
        if item.role == "user":
            msgs.append(HumanMessage(content=item.content))
        else:
            msgs.append(AIMessage(content=item.content))
    return msgs


def get_reply(message: str, history: List[MessageItem],
              context: str = "") -> Tuple[str, int]:
    """
    Génère une réponse LLM via LangChain.

    Args:
        message: Question de l'utilisateur.
        history: Historique de la conversation.
        context: Contexte RAG (vide = mode sans RAG).

    Returns:
        (réponse, tokens_completion_approx)
    """
    lc_history = _to_lc_messages(history)

    if context:
        reply = _chain_rag.invoke({
            "context": context,
            "history": lc_history,
            "question": message,
        })
    else:
        reply = _chain_plain.invoke({
            "history": lc_history,
            "question": message,
        })

    # Supprime les tokens internes des modèles locaux (<|channel|>...<|message|>texte)
    # Certains modèles (Qwen, Mistral fine-tuned) génèrent ces artefacts dans leur sortie
    reply = re.sub(r"<\|[^|]+\|>.*?(?=<\|[^|]+\|>|\Z)", _extract_msg, reply, flags=re.DOTALL)
    reply = reply.strip()

    # Estimation tokens (pas exposé par LangChain LCEL par défaut)
    tokens = max(1, len(reply.split()))
    return reply, tokens


def _extract_msg(m: re.Match) -> str:
    """Garde uniquement le contenu après <|message|> si présent."""
    chunk = m.group(0)
    marker = "<|message|>"
    idx = chunk.find(marker)
    return chunk[idx + len(marker):] if idx != -1 else ""
