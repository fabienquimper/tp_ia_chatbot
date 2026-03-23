"""
Étape 06 — LangChain + RAG
Combine LangChain avec ChromaDB pour un chatbot RAG production-ready.
"""
import os, sys
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, choose_mode

mode = choose_mode()
cfg = CONFIG[mode]
CHROMA_PATH = os.environ.get("CHROMA_PATH", "../etape_05_rag/chroma_db")
COLLECTION_NAME = "techcorp_docs"

# ── LLM ──────────────────────────────────────────────────────────────────────
if cfg["base_url"]:
    llm = ChatOpenAI(model=cfg["model"], base_url=cfg["base_url"], api_key=cfg["api_key"], temperature=0.3)
else:
    llm = ChatOpenAI(model=cfg["model"], api_key=cfg["api_key"], temperature=0.3)

# ── Vector Store ─────────────────────────────────────────────────────────────
if not Path(CHROMA_PATH).exists():
    print(f"✗ Base vectorielle introuvable : {CHROMA_PATH}")
    print("  Lancez d'abord : cd ../etape_05_rag && python indexer.py")
    exit(1)

# Même fonction d'embedding que l'indexeur (all-MiniLM-L6-v2, 100% local)
ef = embedding_functions.DefaultEmbeddingFunction()
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_collection(COLLECTION_NAME, embedding_function=ef)

def retrieve(query: str, k: int = 3):
    results = collection.query(query_texts=[query], n_results=k)
    docs = [{"content": c, "source": m.get("source", "?")}
            for c, m in zip(results["documents"][0], results["metadatas"][0])]
    return docs

# ── Mémoire ──────────────────────────────────────────────────────────────────
K = 3  # 3 échanges (6 messages)
history: list = []

# ── Prompt ───────────────────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system", """Tu es l'assistant virtuel de TechCorp Solutions.
Réponds UNIQUEMENT en te basant sur le contexte fourni.
Si la réponse n'est pas dans le contexte, dis "Je n'ai pas cette information."
Réponds en français, de façon concise et professionnelle.

Contexte : {context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

# ── Chain LCEL ────────────────────────────────────────────────────────────────
chain = prompt | llm | StrOutputParser()

print("=== LangChain RAG — TechCorp (Étape 06) ===")
print(f"Modèle : {cfg['model']} | Base : {CHROMA_PATH}")
print("Comment puis-je vous aider ?\n")

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if not q:
            continue

        try:
            # Récupération des documents pertinents (local, sans OpenAI)
            docs = retrieve(q)
            context = "\n\n".join(d["content"] for d in docs)
            sources = list(set(d["source"] for d in docs))

            # Appel LLM via LCEL
            reply = chain.invoke({"context": context, "history": history, "question": q})

            print(f"IA: {reply}")
            if sources:
                print(f"  [Sources: {', '.join(sources)}]\n")
            else:
                print()

            # Mise à jour de la mémoire
            history.append(HumanMessage(content=q))
            history.append(AIMessage(content=reply))
            if len(history) > K * 2:
                history = history[-K * 2:]

        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
