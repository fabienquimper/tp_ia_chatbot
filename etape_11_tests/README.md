# Étape 11 — Tests avec pytest

## Objectif
Tester chaque brique de l'application. Objectif : 100% green.

## Types de tests

| Type | Fichier | LLM | Vitesse |
|------|---------|-----|---------|
| Unitaires | test_unit.py | Mocké | Très rapide |
| Intégration | test_integration.py | Mocké | Rapide |
| E2E | test_e2e.py | Réel | Lent (ignoré si API off) |

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env  # ou copiez depuis étape 07
```

## Lancer les tests
```bash
# Tous les tests
pytest

# Avec rapport de couverture
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Un fichier spécifique
pytest tests/test_unit.py -v

# Une classe spécifique
pytest tests/test_unit.py::TestSanitize -v

# Tests E2E (API doit être lancée)
uvicorn app.main:app &
pytest tests/test_e2e.py -v
```

## Règle d'or : Toujours mocker le LLM
```python
# ✓ Bon : mock du LLM
@patch("app.llm.get_reply")
def test_chat(mock_llm, client):
    mock_llm.return_value = ("Réponse mock", 10)
    ...

# ✗ Mauvais : vrai appel API
# → 2s d'attente + $0.001 par test
```

## Exercice
1. Lancez `pytest` → tous les tests doivent passer
2. Vérifiez la couverture : `pytest --cov=app`
3. Ajoutez un test pour un nouveau pattern d'injection
4. Lancez l'API et exécutez les tests E2E

# Architecture des tests — les 3 niveaux

```
etape_11_tests/
├── app/                    ← L'application à tester
│   ├── main.py             ← FastAPI : routes /health /chat /history
│   ├── llm.py              ← Appel à l'API LLM
│   ├── database.py         ← SQLite : persistance des messages
│   ├── security.py         ← Sanitisation des inputs
│   └── models.py           ← Schémas Pydantic (ChatRequest, ChatResponse…)
│
└── tests/
    ├── conftest.py         ← Fixtures partagées (DB temp, mock LLM, client)
    ├── test_unit.py        ← Tests unitaires
    ├── test_integration.py ← Tests d'intégration
    └── test_e2e.py         ← Tests end-to-end
```

## test_unit.py — Tests unitaires
- Testent une fonction isolée, sans réseau, sans DB réelle.
- Ex : sanitize_message() dans security.py, les modèles Pydantic, la DB SQLite directement.
- Rapides, toujours reproductibles.

`pytest tests/test_unit.py`

## test_integration.py — Tests d'intégration
- Testent l'API complète mais sans appel réseau réel.
- Utilisent `TestClient` (FastAPI) : simule HTTP en mémoire.
- Le LLM est mocké via `patch("app.main.get_reply")` → zéro appel à Anthropic.
- La DB est une SQLite temporaire (`tmp_path`) recréée à chaque test.
- C'est la couverture principale : rapides + fiables.

`pytest tests/test_integration.py`

## test_e2e.py — Tests end-to-end
- Testent contre le vrai serveur sur `localhost:8000`.
- Skippés automatiquement si le serveur n'est pas lancé (`api_available()`).
- Font de vrais appels à Claude API → peuvent être lents ou échouer si l'API est lente.
- Le `ReadTimeout` que tu as vu est normal : Claude a mis > 30s à répondre.

`pytest tests/test_unit.py`

## conftest.py — La colle
- `use_temp_db` (autouse) : chaque test utilise une DB SQLite isolée dans tmp_path.
- `mock_llm` : patch le LLM pour renvoyer une réponse fixe instantanément.
- `client` : dépend de mock_llm, donc les tests d'intégration ont toujours le mock actif.

## Résumé :

test_unit        → fonction seule           (pas de FastAPI, pas de LLM)
test_integration → FastAPI en mémoire       (LLM mocké, DB temporaire)
test_e2e         → vrai serveur HTTP        (vrai LLM, vraie DB)