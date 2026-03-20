"""
Étape 03 — Memory with Summarization (avancé)
Quand l'historique dépasse MAX_HISTORY, résume les anciens messages
avec le LLM et conserve ce résumé comme contexte compressé.
"""
import os, sys, time
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, choose_mode, make_client

mode = choose_mode()
client = make_client(mode)
MODEL = CONFIG[mode]["model"]
MAX_HISTORY = int(os.environ.get("MAX_HISTORY", "6"))
SUMMARY_TRIGGER = MAX_HISTORY  # Résume quand on dépasse cette limite

history = []
summary = ""  # Résumé compressé des anciens échanges

def summarize_old_messages(messages_to_summarize):
    """Utilise le LLM pour résumer les anciens messages."""
    text = "\n".join(
        f"{'Utilisateur' if m['role']=='user' else 'Assistant'}: {m['content']}"
        for m in messages_to_summarize
    )
    prompt = f"""Voici un historique de conversation. Fais un résumé concis (max 100 mots)
des points clés : sujets abordés, informations importantes, préférences de l'utilisateur.

Historique :
{text}

Résumé :"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"[Résumé de {len(messages_to_summarize)} messages anciens]"

def build_context():
    global history, summary
    system_content = "Tu es un assistant utile et concis. Réponds en français."
    if summary:
        system_content += f"\n\nRésumé de la conversation précédente :\n{summary}"

    # Si l'historique dépasse la limite, on résume les anciens
    if len(history) > SUMMARY_TRIGGER:
        nb_to_summarize = len(history) - MAX_HISTORY // 2
        to_summarize = history[:nb_to_summarize]
        recent = history[nb_to_summarize:]
        print(f"  [Résumé en cours de {len(to_summarize)} messages...]")
        summary = summarize_old_messages(to_summarize)
        history = recent
        system_content += f"\n\nRésumé des échanges précédents :\n{summary}"
        print(f"  [Résumé créé : {summary[:80]}...]\n")

    return [{"role": "system", "content": system_content}] + history

print(f"=== Memory with Summarization — Étape 03 (avancé) ===")
print(f"Modèle : {MODEL} | Max avant résumé : {SUMMARY_TRIGGER} messages\n")
print("Commandes : 'resume' (voir le résumé actuel), 'quit'\n")

try:
    while True:
        q = input("Vous: ").strip()

        if q.lower() in ("quit", "exit", "q"):
            break

        if q.lower() == "resume":
            if summary:
                print(f"\n  Résumé actuel :\n  {summary}\n")
            else:
                print("  Pas encore de résumé (historique court).\n")
            continue

        if not q:
            continue

        history.append({"role": "user", "content": q})
        msgs = build_context()

        start = time.time()
        try:
            response = client.chat.completions.create(model=MODEL, messages=msgs)
        except Exception as e:
            print(f"  ✗ Erreur : {e}\n")
            history.pop()
            continue

        latency = time.time() - start
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})

        print(f"IA: {reply}")
        print(f"  [historique: {len(history)} msgs | résumé: {'oui' if summary else 'non'} | {latency:.2f}s]\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
