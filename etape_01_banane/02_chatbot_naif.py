"""
Étape 01 — Le Chatbot Naïf
Un chatbot fonctionnel en ~10 lignes. Constat : l'IA est amnésique.

OBSERVATION CLÉS :
- Lors de cette session, le chatbot "se souvient" de tout (l'historique est en mémoire)
- Si vous redémarrez le script, toute la mémoire disparaît
- Le LLM lui-même n'a aucune mémoire — c'est NOUS qui gérons l'historique
"""
import os
from dotenv import load_dotenv
import openai

load_dotenv()

q = input("Model ('local' ou 'openai'): ").strip()

if q == "local":
    # On récupère l'URL du moteur ou on utilise l'IP Windows par défaut
    local_url = os.environ.get("LOCAL_BASE_URL", "http://192.168.1.66:1235/v1")
    local_model = os.environ.get("LOCAL_MODEL", "openai/gpt-oss-20b")
    client = openai.OpenAI(base_url=local_url, api_key="lm-studio")
    MODEL = local_model
else:
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "sk-changeme"))
    MODEL = os.environ.get("MODEL", "gpt-4o-mini")

msgs = [{"role": "system", "content": "Tu es un assistant utile et concis. Réponds en français."}]

print("=== Chatbot Naïf — Étape 01 ===")
print("Tapez 'quit' pour quitter.\n")
print("ASTUCE : Dites votre prénom, puis demandez-le à nouveau après redémarrage !\n")

try:
    while True:
        q = input("Vous: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            print("\nAu revoir ! (Relancez le script : je ne me souviendrai de rien...)")
            break
        if not q:
            continue

        msgs.append({"role": "user", "content": q})

        try:
            response = client.chat.completions.create(model=MODEL, messages=msgs)
            reply = response.choices[0].message.content
            print(f"IA: {reply}\n")
            msgs.append({"role": "assistant", "content": reply})

        except openai.AuthenticationError:
            print("ERREUR: Clé API invalide. Vérifiez OPENAI_API_KEY dans .env\n")
            msgs.pop()  # Retirer le message non traité
        except openai.APIConnectionError:
            print("ERREUR: Impossible de contacter l'API. Vérifiez votre connexion internet.\n")
            msgs.pop()
        except openai.RateLimitError:
            print("ERREUR: Limite de débit atteinte. Attendez quelques secondes.\n")
            msgs.pop()
        except Exception as e:
            print(f"ERREUR inattendue: {e}\n")
            msgs.pop()

except KeyboardInterrupt:
    print("\n\nAu revoir ! (Relancez le script : je ne me souviendrai de rien...)")
