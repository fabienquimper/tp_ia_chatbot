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
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

K = 4  # 4 échanges (8 messages)
history: list = []

prompt = ChatPromptTemplate.from_messages([
    ("system", "Tu es un assistant utile et concis. Réponds toujours en français."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

"""
C'est la syntaxe LCEL (LangChain Expression Language). Le | (pipe) connecte les composants : le prompt formate les données, puis les passe au LLM. Équivalent à llm.invoke(prompt.format(...)) mais composable — on pourrait ajouter un parser : prompt | llm | StrOutputParser().
"""
chain = prompt | llm

print(f"\n=== Chatbot LangChain — Étape 06 ===")
print(f"Mémoire : fenêtre glissante K={K} échanges (LCEL)")
print("Commandes : 'memoire' (voir historique), 'reset' (vider), 'quit'\n")

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if q.lower() == "memoire":
            if not history:
                print("\nHistorique : (vide)\n")
            else:
                for msg in history:
                    role = "Vous" if isinstance(msg, HumanMessage) else "IA"
                    print(f"  {role}: {msg.content}")
                print()
            continue

        if q.lower() == "reset":
            history.clear()
            print("  Mémoire effacée.\n")
            continue

        if not q:
            continue

        try:
            reply = chain.invoke({"history": history, "input": q})
            print(f"IA: {reply.content}\n")
            history.append(HumanMessage(content=q))
            history.append(AIMessage(content=reply.content))
            # Fenêtre glissante : garder les K derniers échanges (2*K messages)
            if len(history) > K * 2:
                history = history[-K * 2:]
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
