#!/usr/bin/env python3
"""
Étape 13 — Indexation RAG
Indexe les documents du dossier data/docs/ dans ChromaDB.

Usage :
    python scripts/index_rag.py [--docs-dir data/docs] [--chroma-dir data/chroma_db]
"""
import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def index_documents(docs_dir: str, chroma_dir: str, collection_name: str) -> int:
    """
    Indexe tous les fichiers .txt et .md du dossier docs_dir dans ChromaDB.

    Returns:
        Nombre de chunks indexés.
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        logger.error("chromadb non installé. pip install chromadb")
        sys.exit(1)

    docs_path = Path(docs_dir)
    if not docs_path.exists():
        logger.error("Dossier documents introuvable : %s", docs_dir)
        sys.exit(1)

    # Collecte des fichiers
    files = list(docs_path.glob("*.txt")) + list(docs_path.glob("*.md"))
    if not files:
        logger.warning("Aucun fichier .txt ou .md dans %s", docs_dir)
        return 0

    logger.info("Documents trouvés : %d", len(files))

    # Init ChromaDB
    Path(chroma_dir).mkdir(parents=True, exist_ok=True)
    ef = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=chroma_dir)

    # Supprime la collection existante (re-index propre)
    try:
        client.delete_collection(collection_name)
        logger.info("Collection existante supprimée.")
    except Exception:
        pass

    collection = client.create_collection(collection_name, embedding_function=ef)

    # Chunking et indexation
    documents, metadatas, ids = [], [], []
    chunk_size = 500
    chunk_overlap = 50
    idx = 0

    for fpath in files:
        text = fpath.read_text(encoding="utf-8")
        source = fpath.name
        logger.info("  Indexation : %s (%d chars)", source, len(text))

        # Découpe naïve par paragraphes puis chunks
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        buffer = ""
        for para in paragraphs:
            if len(buffer) + len(para) < chunk_size:
                buffer += para + "\n\n"
            else:
                if buffer:
                    documents.append(buffer.strip())
                    metadatas.append({"source": source})
                    ids.append(f"doc_{idx}")
                    idx += 1
                buffer = para + "\n\n"
        if buffer.strip():
            documents.append(buffer.strip())
            metadatas.append({"source": source})
            ids.append(f"doc_{idx}")
            idx += 1

    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info("Indexation terminée : %d chunks dans '%s'", len(documents), collection_name)
    else:
        logger.warning("Aucun contenu à indexer.")

    return len(documents)


def main():
    parser = argparse.ArgumentParser(description="Indexe des documents dans ChromaDB")
    parser.add_argument("--docs-dir",   default="data/docs",     help="Dossier source")
    parser.add_argument("--chroma-dir", default="data/chroma_db", help="Dossier ChromaDB")
    parser.add_argument("--collection", default="chatbot_docs",  help="Nom de la collection")
    args = parser.parse_args()

    logger.info("=== Indexation RAG ===")
    logger.info("Source  : %s", args.docs_dir)
    logger.info("ChromaDB: %s", args.chroma_dir)
    logger.info("Collection: %s", args.collection)

    n = index_documents(args.docs_dir, args.chroma_dir, args.collection)
    logger.info("Résultat : %d chunks indexés.", n)
    if n == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
