"""
Étape 00 — Le Moteur
Configuration centralisée pour cloud (OpenAI) et local (LM Studio).

Importez ce module depuis n'importe quelle étape pour éviter la duplication :
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'etape_00_moteur'))
    from config import CONFIG, list_configs, make_client, get_client, get_model
"""
import os
from dotenv import load_dotenv
import openai

# Charge toujours depuis ce répertoire, indépendamment du cwd de l'appelant
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

CONFIG = {
    "cloud": {
        "base_url": None,
        "api_key": os.environ.get("OPENAI_API_KEY", "sk-changeme"),
        "model": os.environ.get("CLOUD_MODEL", "gpt-4o-mini"),
        "price_input": 0.00015,   # $/1K tokens
        "price_output": 0.00060,
    },
    "local": {
        "base_url": os.environ.get("LOCAL_BASE_URL", "http://localhost:1234/v1"),
        "api_key": "lm-studio",
        "model": os.environ.get("LOCAL_MODEL", "mistral-7b-instruct"),
        "price_input": 0.0,   # gratuit (local)
        "price_output": 0.0,
    },
    "local_mistral3": {
        "base_url": os.environ.get("LOCAL_BASE_URL", "http://localhost:1234/v1"),
        "api_key": "lm-studio",
        "model": "mistralai/ministral-3-3b",
        "price_input": 0.0,   # gratuit (local)
        "price_output": 0.0,
    },
}


def clean_reply(text: str) -> str:
    """Supprime les tokens de contrôle internes qui fuient dans certains modèles locaux.
    Ex: <|channel|>commentary...<|message|>réponse → réponse"""
    import re
    # Retire tout bloc <|...|> et son contenu jusqu'au dernier <|...|>
    cleaned = re.sub(r"<\|[^|]*\|>[^<]*", "", text)
    # Si le nettoyage a retiré tout le texte, retourner l'original
    return cleaned.strip() or text.strip()


def list_configs() -> list[str]:
    """Retourne la liste des noms de configs disponibles."""
    return list(CONFIG.keys())


def choose_mode() -> str:
    """Sélection interactive du mode. Le MODE du .env est proposé par défaut."""
    configs = list_configs()
    default = os.environ.get("MODE", configs[0])
    if default not in configs:
        default = configs[0]

    print("Configs disponibles :")
    for i, name in enumerate(configs, 1):
        marker = " ← défaut" if name == default else ""
        print(f"  {i}. {name} — modèle : {CONFIG[name]['model']}{marker}")
    choice = input(f"Choisissez (numéro ou nom, Entrée = {default}) : ").strip()

    if not choice:
        return default
    if choice.isdigit() and 1 <= int(choice) <= len(configs):
        return configs[int(choice) - 1]
    if choice in configs:
        return choice
    print(f"  Choix invalide, utilisation de '{default}'")
    return default


def make_client(mode: str) -> openai.OpenAI:
    """Crée un client OpenAI pour la config `mode`."""
    if mode not in CONFIG:
        raise ValueError(f"Mode inconnu : '{mode}'. Disponibles : {list_configs()}")
    cfg = CONFIG[mode]
    if cfg["base_url"]:
        return openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
    return openai.OpenAI(api_key=cfg["api_key"])


def get_client(mode: str = None) -> openai.OpenAI:
    """Retourne un client OpenAI (mode actif par défaut via MODE dans .env)."""
    return make_client(mode or os.environ.get("MODE", "cloud"))


def get_model(mode: str = None) -> str:
    """Retourne le modèle actif (mode actif par défaut via MODE dans .env)."""
    m = mode or os.environ.get("MODE", "cloud")
    if m not in CONFIG:
        m = "cloud"
    return CONFIG[m]["model"]


# Accès direct au mode/config actifs (compat étape 00)
MODE = os.environ.get("MODE", "cloud")
if MODE not in CONFIG:
    print(f"[ATTENTION] MODE='{MODE}' inconnu, utilisation de 'cloud' par défaut.")
    MODE = "cloud"
ACTIVE = CONFIG[MODE]


if __name__ == "__main__":
    print(f"Mode actif : {MODE}")
    print(f"Modèle     : {get_model()}")
    if ACTIVE["base_url"]:
        print(f"Base URL   : {ACTIVE['base_url']}")
    else:
        print(f"Base URL   : (OpenAI par défaut)")
