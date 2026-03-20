"""
Étape 06 — LangChain
Refactorisation du chatbot avec LangChain.
Avantage : swap Cloud/Local en 1 ligne.
"""
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("MODEL", "gpt-4o-mini")
MODE = os.environ.get("MODE", "cloud")
API_KEY = os.environ.get("OPENAI_API_KEY", "sk-changeme")
LM_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")

# ── Choix du LLM (1 ligne pour switcher) ─────────────────────────────────────
if MODE == "local":
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        model=MODEL,
        base_url=LM_URL,
        api_key="lm-studio",
        temperature=0.7
    )
    print(f"Mode LOCAL : {LM_URL}")
else:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model=MODEL, api_key=API_KEY, temperature=0.7)
    print(f"Mode CLOUD : {MODEL}")

# ── Mémoire avec fenêtre glissante ───────────────────────────────────────────
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

memory = ConversationBufferWindowMemory(
    k=4,  # 4 échanges (8 messages)
    return_messages=False
)

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "input"],
    template="""Tu es un assistant utile et concis. Réponds toujours en français.

Historique de conversation :
{history}

Utilisateur: {input}
Assistant:"""
)

chain = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=PROMPT_TEMPLATE,
    verbose=False
)

print(f"\n=== Chatbot LangChain — Étape 06 ===")
print(f"Mémoire : 4 échanges (ConversationBufferWindowMemory)")
print("Commandes : 'memoire' (voir historique), 'reset' (vider), 'quit'\n")

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if q.lower() == "memoire":
            history = memory.load_memory_variables({})
            print(f"\nHistorique :\n{history.get('history', '(vide)')}\n")
            continue

        if q.lower() == "reset":
            memory.clear()
            print("  Mémoire effacée.\n")
            continue

        if not q:
            continue

        try:
            reply = chain.predict(input=q)
            print(f"IA: {reply}\n")
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
