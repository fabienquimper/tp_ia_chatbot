"""
Étape 06 — LangChain
Refactorisation du chatbot avec LangChain.
Avantage : swap Cloud/Local en 1 ligne.
"""
import os, sys
from langchain_openai import ChatOpenAI

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, choose_mode

mode = choose_mode()
cfg = CONFIG[mode]

# ── Choix du LLM (1 ligne pour switcher) ─────────────────────────────────────
if cfg["base_url"]:
    llm = ChatOpenAI(model=cfg["model"], base_url=cfg["base_url"], api_key=cfg["api_key"], temperature=0.7)
    print(f"Mode LOCAL : {cfg['base_url']}")
else:
    llm = ChatOpenAI(model=cfg["model"], api_key=cfg["api_key"], temperature=0.7)
    print(f"Mode CLOUD : {cfg['model']}")

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
