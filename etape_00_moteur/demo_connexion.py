"""
Étape 00 — Démo de connexion
Teste les connexions cloud (OpenAI) et local (LM Studio) et affiche les résultats.
"""
import os
import time
from dotenv import load_dotenv
import openai

load_dotenv()

TEST_PROMPT = "Réponds juste 'OK' en un mot."

def test_connection(name: str, base_url, api_key: str, model: str) -> dict:
    """Teste une connexion LLM et retourne les résultats."""
    result = {
        "name": name,
        "model": model,
        "success": False,
        "reply": None,
        "latency": None,
        "error": None,
    }

    try:
        if base_url:
            client = openai.OpenAI(base_url=base_url, api_key=api_key)
        else:
            client = openai.OpenAI(api_key=api_key)

        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": TEST_PROMPT}],
            max_tokens=10,
            timeout=15,
        )
        result["latency"] = round(time.time() - start, 3)
        result["reply"] = response.choices[0].message.content.strip()
        result["success"] = True

    except openai.AuthenticationError:
        result["error"] = "Clé API invalide ou manquante"
    except openai.APIConnectionError:
        result["error"] = "Impossible de se connecter au serveur"
    except openai.APITimeoutError:
        result["error"] = "Timeout — le serveur ne répond pas"
    except Exception as e:
        result["error"] = str(e)

    return result


def print_result(res: dict):
    status = "OK" if res["success"] else "ECHEC"
    print(f"\n  [{status}] {res['name']} — modèle: {res['model']}")
    if res["success"]:
        print(f"        Réponse  : {res['reply']}")
        print(f"        Latence  : {res['latency']}s")
    else:
        print(f"        Erreur   : {res['error']}")


def main():
    print("=" * 55)
    print("  Étape 00 — Test de Connexion au Moteur LLM")
    print("=" * 55)

    results = []

    # Test 1 : OpenAI Cloud
    print("\n[1/2] Test connexion CLOUD (OpenAI)...")
    api_key = os.environ.get("OPENAI_API_KEY", "sk-changeme")
    r1 = test_connection(
        name="Cloud OpenAI",
        base_url=None,
        api_key=api_key,
        model="gpt-4o-mini",
    )
    print_result(r1)
    results.append(r1)

    # Test 2 : LM Studio Local
    print("\n[2/2] Test connexion LOCAL (LM Studio)...")
    
    # On récupère l'URL du moteur ou on utilise l'IP Windows par défaut
    local_url = os.environ.get("LOCAL_BASE_URL", "http://192.168.1.66:1235/v1")
    local_model = os.environ.get("LOCAL_MODEL", "openai/gpt-oss-20b")

    r2 = test_connection(
        name="Local LM Studio",
        base_url=local_url,
        api_key="lm-studio",
        model=local_model,
    )
    print_result(r2)
    results.append(r2)

    # Résumé
    print("\n" + "=" * 55)
    print("  RÉSUMÉ")
    print("=" * 55)
    working = [r for r in results if r["success"]]
    if not working:
        print("\n  ATTENTION : Aucune connexion ne fonctionne !")
        print("  → Vérifiez votre OPENAI_API_KEY dans .env")
        print("  → Ou démarrez LM Studio avec le serveur local")
    else:
        print(f"\n  {len(working)}/{len(results)} connexion(s) opérationnelle(s)")
        print(f"\n  Recommandation MODE:")
        if r1["success"]:
            print("    MODE=cloud  ← OpenAI fonctionne")
        if r2["success"]:
            print("    MODE=local  ← LM Studio fonctionne")
    print()


if __name__ == "__main__":
    main()
