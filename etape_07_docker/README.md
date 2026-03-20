# Étape 07 — Docker & FastAPI

## Objectif
Rendre le chatbot accessible via une API REST, containerisé avec Docker.

## Architecture
```
Client HTTP → FastAPI → LLM (OpenAI)
                ↕
             SQLite
```

## Endpoints
| Méthode | URL | Description |
|---------|-----|-------------|
| GET | /health | Health check |
| POST | /chat | Envoyer un message |
| GET | /history/{session_id} | Historique d'une session |
| GET | /sessions | Lister les sessions |
| GET | /docs | Documentation Swagger (auto) |

## Installation

### Sans Docker
```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### Avec Docker
```bash
cp .env.example .env
# Éditez .env avec votre clé API
docker build -t chatbot .
docker run -p 8000:8000 --env-file .env chatbot
```

### Avec Docker Compose
```bash
docker-compose up --build
```

## Test
```bash
# Swagger UI
open http://localhost:8000/docs

# Script de test curl
bash test_api.sh

# Health check
curl http://localhost:8000/health
```

## Exercice
1. Lancez l'API (`uvicorn app.main:app --reload`)
2. Ouvrez Swagger : http://localhost:8000/docs
3. Testez `/chat` avec votre nom
4. Testez `/chat` avec "Comment je m'appelle ?"
5. Vérifiez `/history/{session_id}`
6. Buildez et lancez avec Docker
7. Ajoutez un endpoint `DELETE /history/{session_id}`
