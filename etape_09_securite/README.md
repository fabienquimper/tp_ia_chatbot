# Étape 09 — Sécurité

## Objectif
Protéger le chatbot contre les abus : injection, rate limiting, authentification.

## Couches de sécurité

| Couche | Technologie | Protection |
|--------|-------------|------------|
| Rate Limit | slowapi | 10 req/min/IP pour /chat |
| Auth | JWT (python-jose) | Token Bearer obligatoire |
| CORS | FastAPI middleware | Origines restreintes |
| Prompt Guard | Regex patterns | 10+ patterns d'injection |
| Sanitization | html.escape | XSS prevention |
| Secrets | python-dotenv | Jamais dans le code |

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Utilisation

### 1. Obtenir un token
```bash
curl -X POST http://localhost:8000/auth/token \
  -d "username=alice&password=password123"
```
Utilisateurs de démo : alice/password123, bob/secret456, admin/admin789

### 2. Appeler /chat avec le token
```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour !", "session_id": "ma-session"}'
```

## Tests de sécurité
```bash
python test_security.py
```

## Exercice
1. Lancez l'API
2. Exécutez `python test_security.py`
3. Vérifiez que les injections sont bloquées (403)
4. Essayez de dépasser le rate limit
5. Bonus : ajoutez un nouveau pattern d'injection dans `security.py`

## Règle d'or CORS
```python
# JAMAIS en production :
allow_origins=["*"]

# TOUJOURS restreindre :
allow_origins=["https://monsite.fr"]
```
