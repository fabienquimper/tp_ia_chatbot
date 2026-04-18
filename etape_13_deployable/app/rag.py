"""
Étape 13 — RAG (Retrieval-Augmented Generation)
Recherche vectorielle avec ChromaDB. Optionnel : si la base n'existe pas,
l'app fonctionne sans RAG (mode dégradé gracieux).
"""
import os
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_CHROMA = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
CHROMA_PATH = os.environ.get("CHROMA_PATH", _DEFAULT_CHROMA)
COLLECTION_NAME = os.environ.get("RAG_COLLECTION", "chatbot_docs")
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "3"))

_collection = None
_rag_available = False


def init_rag() -> bool:
    """Initialise la connexion ChromaDB. Retourne True si disponible."""
    global _collection, _rag_available

    if not Path(CHROMA_PATH).exists():
        logger.warning("RAG désactivé : base vectorielle introuvable (%s)", CHROMA_PATH)
        logger.warning("Lancez scripts/index_rag.py pour créer la base vectorielle.")
        _rag_available = False
        return False

    try:
        import chromadb
        from chromadb.utils import embedding_functions

        ef = embedding_functions.DefaultEmbeddingFunction()
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION_NAME, embedding_function=ef)
        count = _collection.count()
        logger.info("RAG activé : collection '%s' (%d documents)", COLLECTION_NAME, count)
        _rag_available = True
        return True
    except Exception as e:
        logger.warning("RAG désactivé : %s", e)
        _rag_available = False
        return False


def is_available() -> bool:
    if not _rag_available and Path(CHROMA_PATH).exists():
        init_rag()
    return _rag_available


def retrieve(query: str, k: int = RAG_TOP_K) -> List[dict]:
    """
    Recherche les k documents les plus pertinents pour la requête.

    Returns:
        Liste de dicts {"content": str, "source": str}
    """
    if not _rag_available or _collection is None:
        return []

    results = _collection.query(query_texts=[query], n_results=k)
    docs = [
        {"content": c, "source": m.get("source", "?")}
        for c, m in zip(results["documents"][0], results["metadatas"][0])
    ]
    return docs


def build_context(docs: List[dict]) -> str:
    """Construit le contexte textuel à injecter dans le prompt."""
    if not docs:
        return ""
    return "\n\n---\n\n".join(d["content"] for d in docs)
