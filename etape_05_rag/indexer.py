"""
Étape 05 — Indexeur de documents
Charge les documents du dossier data/ et les indexe dans ChromaDB.
"""
import os, re
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
DATA_DIR = Path("./data")
COLLECTION_NAME = "techcorp_docs"

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Découpe le texte en chunks avec chevauchement."""
    # Découpe d'abord par paragraphes
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += (" " if current_chunk else "") + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # Si le paragraphe est trop long, le découper
            if len(para) > chunk_size:
                words = para.split()
                sub = ""
                for word in words:
                    if len(sub) + len(word) <= chunk_size:
                        sub += (" " if sub else "") + word
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = word
                if sub:
                    current_chunk = sub
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def load_documents(data_dir: Path) -> list[dict]:
    """Charge tous les .txt du dossier data/."""
    docs = []
    for filepath in sorted(data_dir.glob("*.txt")):
        text = filepath.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            docs.append({
                "id": f"{filepath.stem}_{i:03d}",
                "text": chunk,
                "source": filepath.name,
                "chunk_index": i
            })
        print(f"  {filepath.name} → {len(chunks)} chunks")
    return docs

def index_documents():
    """Indexe tous les documents dans ChromaDB."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Utilise les embeddings par défaut (all-MiniLM-L6-v2)
    ef = embedding_functions.DefaultEmbeddingFunction()

    # Supprime la collection si elle existe
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' supprimée (réindexation).")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"\nChargement des documents depuis {DATA_DIR}...")
    docs = load_documents(DATA_DIR)

    if not docs:
        print("✗ Aucun document trouvé dans data/")
        return

    print(f"\nIndexation de {len(docs)} chunks...")
    # Indexation par lots
    batch_size = 50
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        collection.add(
            ids=[d["id"] for d in batch],
            documents=[d["text"] for d in batch],
            metadatas=[{"source": d["source"], "chunk_index": d["chunk_index"]} for d in batch]
        )
        print(f"  Lot {i//batch_size + 1}/{(len(docs)-1)//batch_size + 1} indexé")

    print(f"\n✓ {len(docs)} chunks indexés dans '{CHROMA_PATH}'")
    print(f"  Collection : {COLLECTION_NAME}")

    # Test rapide
    results = collection.query(query_texts=["prix abonnement"], n_results=2)
    print(f"\nTest de recherche 'prix abonnement' :")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  [{meta['source']}] {doc[:100]}...")

if __name__ == "__main__":
    index_documents()
