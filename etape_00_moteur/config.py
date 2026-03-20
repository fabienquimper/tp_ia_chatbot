"""
Étape 00 — Le Moteur
Configuration centralisée pour cloud (OpenAI) et local (LM Studio).
"""
import os
from dotenv import load_dotenv
import openai

load_dotenv()

CONFIG = {
    "cloud": {
        "base_url": None,
        "api_key": os.environ.get("OPENAI_API_KEY", "sk-changeme"),
        "model": "gpt-4o-mini",
    },
    "local": {
        "base_url": "http://192.168.1.66:1235/v1",
        #"base_url": "http://localhost:1234/v1",
        "api_key": "lm-studio",
        "model": "mistral-7b-instruct",
    },
}

MODE = os.environ.get("MODE", "cloud")

if MODE not in CONFIG:
    print(f"[ATTENTION] MODE='{MODE}' inconnu, utilisation de 'cloud' par défaut.")
    MODE = "cloud"

ACTIVE = CONFIG[MODE]


def get_client() -> openai.OpenAI:
    """Retourne un client OpenAI configuré selon le MODE actif."""
    if ACTIVE["base_url"]:
        return openai.OpenAI(base_url=ACTIVE["base_url"], api_key=ACTIVE["api_key"])
    return openai.OpenAI(api_key=ACTIVE["api_key"])


def get_model() -> str:
    """Retourne le nom du modèle actif."""
    return ACTIVE["model"]


if __name__ == "__main__":
    print(f"Mode actif : {MODE}")
    print(f"Modèle     : {get_model()}")
    if ACTIVE["base_url"]:
        print(f"Base URL   : {ACTIVE['base_url']}")
    else:
        print(f"Base URL   : (OpenAI par défaut)")
