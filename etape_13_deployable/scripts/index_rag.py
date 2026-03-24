#!/usr/bin/env python3
"""
Étape 13 — Indexation RAG
Indexe les documents du dossier data/docs/ dans ChromaDB.

Usage :
    python scripts/index_rag.py [--docs-dir data/docs] [--chroma-dir data/chroma_db]

Méthodes de chunking disponibles (variable CHUNK_METHOD) :
  "paragraph" — découpe par paragraphes (~600 chars). Simple, robuste.
                 Inconvénient : mélange plusieurs sujets dans un même chunk.
  "section"   — découpe selon les marqueurs == Section == et --- Sous-section ---.
                 Chaque chunk reste centré sur un seul sujet → meilleure précision RAG.
"""
import os
import re
import sys
import argparse
import logging
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Méthode de chunking ────────────────────────────────────────────────────
# Changer cette valeur pour comparer les deux stratégies :
#   "paragraph" → simple, classique (score eval ~8/15 avec k=5)
#   "section"   → basé sur la structure des docs (score eval attendu > 10/15)
CHUNK_METHOD = "section"

# Taille max d'un chunk en mode "paragraph" (caractères)
PARAGRAPH_CHUNK_SIZE = 600


def _chunk_by_paragraphs(text: str, chunk_size: int = PARAGRAPH_CHUNK_SIZE) -> List[str]:
    """
    Découpe le texte en blocs de ~chunk_size caractères.
    Stratégie classique : accumulation de paragraphes consécutifs.
    Avantage  : simple, ne dépend pas d'une structure particulière.
    Inconvénient : peut mélanger plusieurs sujets dans un même chunk,
                   ce qui dilue les embeddings.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) < chunk_size:
            buffer += para + "\n\n"
        else:
            if buffer:
                chunks.append(buffer.strip())
            buffer = para + "\n\n"
    if buffer.strip():
        chunks.append(buffer.strip())
    return chunks


def _chunk_by_sections(text: str, max_chunk: int = 1200) -> List[str]:
    """
    Découpe le texte selon les marqueurs structurels des documents TechCorp :
      == Titre de section ==   → sections principales
      --- Titre sous-section --- → sous-sections à l'intérieur d'une section

    Chaque chunk contient :
      - le titre de sa section principale (contexte)
      - éventuellement le titre de la sous-section
      - le contenu correspondant

    Avantage  : chaque chunk reste sémantiquement cohérent (un seul sujet).
                Les embeddings sont plus précis → meilleur recall RAG.
    Inconvénient : suppose que les documents respectent ce format de balisage.

    Si un bloc dépasse max_chunk caractères, il est subdivisé par paragraphes.
    """
    # Découpe sur les sections principales == ... ==
    section_pattern = re.compile(r"^==\s*(.+?)\s*==\s*$", re.MULTILINE)
    parts = section_pattern.split(text)
    # parts = [texte_avant, titre1, contenu1, titre2, contenu2, ...]

    chunks = []
    # Texte avant la première section (titre du document, intro)
    intro = parts[0].strip()
    if intro:
        chunks.append(intro)

    # Itération sur chaque section
    for i in range(1, len(parts), 2):
        section_title = parts[i].strip()
        section_body = parts[i + 1] if i + 1 < len(parts) else ""

        # Découpe sur les sous-sections --- ... ---
        sub_pattern = re.compile(r"^---\s*(.+?)\s*---\s*$", re.MULTILINE)
        sub_parts = sub_pattern.split(section_body)
        # sub_parts = [texte_avant_premiere_sous_section, titre_sub1, contenu_sub1, ...]

        # Texte de la section avant toute sous-section
        pre_sub = sub_parts[0].strip()
        if pre_sub:
            chunk = f"== {section_title} ==\n\n{pre_sub}"
            chunks.extend(_split_if_large(chunk, max_chunk, section_title))

        for j in range(1, len(sub_parts), 2):
            sub_title = sub_parts[j].strip()
            sub_body = sub_parts[j + 1].strip() if j + 1 < len(sub_parts) else ""
            if sub_body:
                chunk = f"== {section_title} ==\n--- {sub_title} ---\n\n{sub_body}"
                chunks.extend(_split_if_large(chunk, max_chunk, section_title, sub_title))

    return [c for c in chunks if c.strip()]


def _split_if_large(chunk: str, max_chunk: int,
                    section_title: str, sub_title: str = "") -> List[str]:
    """Si chunk dépasse max_chunk, le subdivise par paragraphes en conservant le contexte."""
    if len(chunk) <= max_chunk:
        return [chunk]

    header = f"== {section_title} =="
    if sub_title:
        header += f"\n--- {sub_title} ---"

    paragraphs = [p.strip() for p in chunk.split("\n\n") if p.strip()]
    result = []
    buffer = header
    for para in paragraphs:
        if para.startswith("==") or para.startswith("---"):
            continue  # skip les lignes de titre déjà dans le header
        if len(buffer) + len(para) < max_chunk:
            buffer += "\n\n" + para
        else:
            if buffer.strip() != header.strip():
                result.append(buffer.strip())
            buffer = header + "\n\n" + para
    if buffer.strip() != header.strip():
        result.append(buffer.strip())
    return result if result else [chunk]


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

    logger.info("Documents trouvés : %d  (méthode : %s)", len(files), CHUNK_METHOD)

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
    idx = 0

    for fpath in files:
        text = fpath.read_text(encoding="utf-8")
        source = fpath.name
        logger.info("  Indexation : %s (%d chars)", source, len(text))

        if CHUNK_METHOD == "section":
            chunks = _chunk_by_sections(text)
        else:
            chunks = _chunk_by_paragraphs(text)

        logger.info("    → %d chunks", len(chunks))
        for chunk in chunks:
            if chunk:
                documents.append(chunk)
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
    parser.add_argument("--method",     default=None,
                        choices=["paragraph", "section"],
                        help="Méthode de chunking (écrase CHUNK_METHOD)")
    args = parser.parse_args()

    if args.method:
        global CHUNK_METHOD
        CHUNK_METHOD = args.method

    logger.info("=== Indexation RAG ===")
    logger.info("Source    : %s", args.docs_dir)
    logger.info("ChromaDB  : %s", args.chroma_dir)
    logger.info("Collection: %s", args.collection)
    logger.info("Méthode   : %s", CHUNK_METHOD)

    n = index_documents(args.docs_dir, args.chroma_dir, args.collection)
    logger.info("Résultat : %d chunks indexés.", n)
    if n == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
