"""
Étape 12 — LLM-as-Judge
Utilise un LLM pour évaluer la qualité des réponses.
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etape_00_moteur"))
from config import CONFIG, make_client

# Le juge utilise le cloud par défaut, ou un modèle local si JUDGE_MODE est défini
JUDGE_MODE = os.environ.get("JUDGE_MODE", "cloud")
if JUDGE_MODE not in CONFIG:
    JUDGE_MODE = "cloud"
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", CONFIG[JUDGE_MODE]["model"])

_judge_client = None

def get_judge_client():
    global _judge_client
    if _judge_client is None:
        _judge_client = make_client(JUDGE_MODE)
    return _judge_client

JUDGE_PROMPT = """Tu es un expert en évaluation de réponses de modèles de langage.
Évalue la réponse suivante sur les critères ci-dessous. Réponds UNIQUEMENT avec un JSON.

Question : {question}
Réponse à évaluer : {answer}

Critères (note de 1 à 10 chacun) :
- pertinence : la réponse répond-elle à la question ?
- exactitude : les informations sont-elles correctes ?
- concision : la réponse est-elle concise sans être trop courte ?

Réponds avec ce format JSON exact :
{{"pertinence": <1-10>, "exactitude": <1-10>, "concision": <1-10>, "commentaire": "<max 50 mots>"}}"""

def judge_with_llm(question: str, answer: str) -> dict:
    """
    Évalue une réponse avec un LLM.
    Retourne {"pertinence": X, "exactitude": X, "concision": X, "score": X, "commentaire": "..."}
    """
    try:
        client = get_judge_client()
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{
                "role": "user",
                "content": JUDGE_PROMPT.format(question=question, answer=answer)
            }],
            response_format={"type": "json_object"},
            max_tokens=200
        )
        import json
        result = json.loads(response.choices[0].message.content)
        score = (result.get("pertinence", 5) + result.get("exactitude", 5) + result.get("concision", 5)) / 3
        result["score"] = round(score, 1)
        return result
    except Exception as e:
        return {"pertinence": 5, "exactitude": 5, "concision": 5, "score": 5.0, "commentaire": f"Erreur: {e}"}

def judge_with_keywords(question: str, answer: str, expected_keywords: list) -> dict:
    """
    Évaluation de repli basée sur les mots-clés (pas d'API requise).
    """
    answer_lower = answer.lower()
    found = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    hit_rate = len(found) / len(expected_keywords) if expected_keywords else 0
    score = round(hit_rate * 10, 1)
    return {
        "pertinence": score,
        "exactitude": score,
        "concision": 7.0,  # On ne peut pas évaluer sans LLM
        "score": score,
        "commentaire": f"Mots-clés trouvés: {found} / {expected_keywords}",
        "method": "keywords"
    }
