"""
Étape 05 — RAG avec ChromaDB
Chatbot qui répond en se basant sur la base de connaissances TechCorp.
"""
import os, sys, time
from pathlib import Path
import openai
import chromadb
from chromadb.utils import embedding_functions

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, choose_mode, make_client

mode = choose_mode()
client = make_client(mode)
MODEL = CONFIG[mode]["model"]
CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
N_RESULTS = int(os.environ.get("N_RESULTS", "3"))
COLLECTION_NAME = "techcorp_docs"

# Connexion ChromaDB
def load_collection():
    if not Path(CHROMA_PATH).exists():
        print("✗ Base vectorielle introuvable. Lancez d'abord : python indexer.py")
        exit(1)
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.DefaultEmbeddingFunction()
    try:
        return chroma_client.get_collection(name=COLLECTION_NAME, embedding_function=ef)
    except Exception:
        print(f"✗ Collection '{COLLECTION_NAME}' introuvable. Lancez : python indexer.py")
        exit(1)

collection = load_collection()

def retrieve_context(query: str, n: int = N_RESULTS) -> tuple[str, list[str]]:
    """Récupère les chunks pertinents pour la question."""
    results = collection.query(query_texts=[query], n_results=n)
    docs = results["documents"][0]
    sources = [m["source"] for m in results["metadatas"][0]]
    distances = results["distances"][0]

    context_parts = []
    for doc, source, dist in zip(docs, sources, distances):
        relevance = 1 - dist  # cosine: plus proche = plus pertinent
        context_parts.append(f"[Source: {source}, Pertinence: {relevance:.0%}]\n{doc}")

    context = "\n\n---\n\n".join(context_parts)
    return context, list(set(sources))

def build_rag_prompt(context: str) -> str:
    return f"""Tu es l'assistant virtuel de TechCorp Solutions.
Réponds UNIQUEMENT en te basant sur le contexte fourni.
Si la réponse n'est pas dans le contexte, dis "Je n'ai pas cette information dans ma base de connaissances."
Réponds toujours en français, de façon concise et professionnelle.

CONTEXTE :
{context}
"""

history = []

print("=== RAG Chatbot — TechCorp Solutions (Étape 05) ===")
print(f"Base vectorielle : {CHROMA_PATH} | {collection.count()} chunks indexés")
print(f"Modèle : {MODEL} | Documents récupérés : {N_RESULTS}")
print("\nJe suis l'assistant TechCorp. Comment puis-je vous aider ?")
print("Commandes : 'contexte' (voir le dernier contexte RAG), 'quit'\n")

last_context = ""
last_sources = []

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if q.lower() == "contexte":
            if last_context:
                print(f"\nDernier contexte RAG (sources : {last_sources}):")
                print(f"{last_context[:500]}...\n")
            else:
                print("  Pas encore de contexte. Posez une question d'abord.\n")
            continue

        if not q:
            continue

        # 1. Récupération des documents pertinents
        t_retrieve = time.time()
        context, sources = retrieve_context(q)
        retrieve_time = time.time() - t_retrieve
        last_context = context
        last_sources = sources

        # 2. Construction du prompt RAG
        system_prompt = build_rag_prompt(context)

        # 3. Construction des messages avec historique court
        history.append({"role": "user", "content": q})
        msgs = [
            {"role": "system", "content": system_prompt}
        ] + history[-6:]  # 3 échanges max

        # 4. Appel LLM
        t_llm = time.time()
        try:
            response = client.chat.completions.create(model=MODEL, messages=msgs)
        except openai.AuthenticationError:
            print("  ✗ Clé API invalide.\n")
            history.pop()
            continue
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")
            history.pop()
            continue
        llm_time = time.time() - t_llm

        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})

        print(f"IA: {reply}")
        print(f"  [Sources: {', '.join(sources)} | Récup: {retrieve_time:.2f}s | LLM: {llm_time:.2f}s]\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
