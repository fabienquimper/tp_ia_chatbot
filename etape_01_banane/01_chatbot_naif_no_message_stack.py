"""
Étape 01 — Le Chatbot SANS historique (version naïve)
Démontre le problème d'amnésie : chaque appel est indépendant.
Le LLM ne reçoit jamais les échanges précédents → il ne peut pas se souvenir.

OBSERVATION CLÉS :
- Le message utilisateur N'EST PAS ajouté à msgs avant l'appel
- Chaque appel reçoit uniquement le system prompt → amnésie totale
- Comparez avec 02_chatbot_naif.py qui accumule l'historique
"""
import os, sys
import openai

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, choose_mode, make_client

mode = choose_mode()
client = make_client(mode)
MODEL = CONFIG[mode]["model"]

# msgs contient SEULEMENT le system prompt — jamais mis à jour
msgs = [{"role": "system", "content": "Tu es un assistant utile et concis. Réponds en français."}]

print("=== Chatbot SANS Historique — Étape 01 (version 1/2) ===")
print("Ce chatbot ne se souvient de RIEN, même dans la même session !")
print("Tapez 'quit' pour quitter.\n")
print("ASTUCE : Dites votre prénom, puis demandez-le → il ne saura pas répondre !\n")

try:
    while True:
        q = input("Vous: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            print("\nAu revoir !")
            break
        if not q:
            continue

        # On envoie la question en one-shot, sans l'ajouter à msgs
        messages_one_shot = msgs + [{"role": "user", "content": q}]

        try:
            response = client.chat.completions.create(model=MODEL, messages=messages_one_shot)
            reply = response.choices[0].message.content
            print(f"IA: {reply}\n")
            # NOTE : on ne fait RIEN avec reply → prochain appel = même contexte vide

        except openai.AuthenticationError:
            print("ERREUR: Clé API invalide. Vérifiez OPENAI_API_KEY dans etape_00_moteur/.env\n")
        except openai.APIConnectionError:
            print("ERREUR: Impossible de contacter l'API. Vérifiez votre connexion internet.\n")
        except openai.RateLimitError:
            print("ERREUR: Limite de débit atteinte. Attendez quelques secondes.\n")
        except Exception as e:
            print(f"ERREUR inattendue: {e}\n")

except KeyboardInterrupt:
    print("\n\nAu revoir !")
