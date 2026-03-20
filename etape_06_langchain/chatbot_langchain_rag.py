"""
Étape 06 — LangChain + RAG
Combine LangChain avec ChromaDB pour un chatbot RAG production-ready.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
CHROMA_PATH = os.environ.get("CHROMA_PATH", "../etape_05_rag/chroma_db")
COLLECTION_NAME = "techcorp_docs"

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate

# ── LLM ──────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(model=MODEL, api_key=API_KEY, temperature=0.3)

# ── Vector Store ─────────────────────────────────────────────────────────────
if not Path(CHROMA_PATH).exists():
    print(f"✗ Base vectorielle introuvable : {CHROMA_PATH}")
    print("  Lancez d'abord : cd ../etape_05_rag && python indexer.py")
    exit(1)

embeddings = OpenAIEmbeddings(api_key=API_KEY)
vectorstore = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=CHROMA_PATH
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ── Mémoire ──────────────────────────────────────────────────────────────────
memory = ConversationBufferWindowMemory(
    k=3,
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

# ── Prompt ───────────────────────────────────────────────────────────────────
QA_PROMPT = PromptTemplate(
    template="""Tu es l'assistant virtuel de TechCorp Solutions.
Réponds UNIQUEMENT en te basant sur le contexte fourni.
Si la réponse n'est pas dans le contexte, dis "Je n'ai pas cette information."
Réponds en français, de façon concise et professionnelle.

Contexte : {context}

Historique : {chat_history}

Question : {question}
Réponse :""",
    input_variables=["context", "chat_history", "question"]
)

# ── Chain ─────────────────────────────────────────────────────────────────────
rag_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    combine_docs_chain_kwargs={"prompt": QA_PROMPT},
    return_source_documents=True,
    verbose=False
)

print("=== LangChain RAG — TechCorp (Étape 06) ===")
print(f"Modèle : {MODEL} | Base : {CHROMA_PATH}")
print("Comment puis-je vous aider ?\n")

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if not q:
            continue

        try:
            result = rag_chain({"question": q})
            reply = result["answer"]
            source_docs = result.get("source_documents", [])
            sources = list(set(d.metadata.get("source", "?") for d in source_docs))

            print(f"IA: {reply}")
            if sources:
                print(f"  [Sources: {', '.join(sources)}]\n")
            else:
                print()
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
