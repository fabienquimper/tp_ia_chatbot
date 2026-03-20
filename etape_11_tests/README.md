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
