.PHONY: help dev prod test build clean index-rag logs stop eval eval-verbose smoke smoke-no-rag

# Variables
IMAGE  := chatbot-api
TAG    := $(shell git rev-parse --short HEAD 2>/dev/null || echo latest)
COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  IMAGE=$(IMAGE)  TAG=$(TAG)"

# ── Développement ─────────────────────────────────────────────────────────────
dev:  ## Lance la stack de développement (API + Prometheus + Grafana)
	$(COMPOSE) up --build

dev-bg:  ## Lance en arrière-plan
	$(COMPOSE) up --build -d

# ── Tests ─────────────────────────────────────────────────────────────────────
test:  ## Lance les tests dans Docker (build stage 'test')
	docker build --target test -t $(IMAGE):test .

test-local:  ## Lance les tests localement (nécessite Python + deps)
	pip install -q -r requirements-dev.txt
	pytest tests/ -v --cov=app --cov-report=term-missing

test-security:  ## Analyse de sécurité statique (bandit)
	pip install -q bandit
	bandit -r app/ -ll

# ── Production ────────────────────────────────────────────────────────────────
prod:  ## Lance la stack de production avec Nginx
	$(COMPOSE) -f docker-compose.prod.yml up -d --build

build:  ## Construit l'image de production (avec tests)
	./build.sh

build-skip-tests:  ## Construit sans tests (urgence seulement)
	./build.sh --skip-tests

# ── Évaluation ────────────────────────────────────────────────────────────────
eval:  ## Évaluation complète : 15 questions avec vérification des mots-clés
	python scripts/eval.py --eval-file data/eval_set.jsonl

eval-verbose:  ## Évaluation complète avec réponses complètes affichées
	python scripts/eval.py --eval-file data/eval_set.jsonl --verbose

smoke:  ## Smoke test : 5 questions rapides pour vérifier que l'API répond
	python scripts/eval.py --eval-file data/eval_set.jsonl --count 5 --shuffle

smoke-no-rag:  ## Smoke test sans RAG
	python scripts/eval.py --eval-file data/eval_set.jsonl --count 5 --no-rag

# ── RAG ───────────────────────────────────────────────────────────────────────
index-rag:  ## Indexe les documents data/docs/ dans ChromaDB
	python scripts/index_rag.py

index-rag-docker:  ## Indexe le RAG dans le conteneur Docker (docs/ baked dans l'image)
	$(COMPOSE) exec chatbot python scripts/index_rag.py --docs-dir docs

# ── Opérations ────────────────────────────────────────────────────────────────
logs:  ## Affiche les logs de l'API
	$(COMPOSE) logs -f chatbot

stop:  ## Arrête tous les services
	$(COMPOSE) down

clean:  ## Supprime conteneurs, volumes et images de build
	$(COMPOSE) down -v --rmi local
	docker image rm $(IMAGE):test 2>/dev/null || true

status:  ## Affiche le statut des services
	$(COMPOSE) ps
	@echo ""
	@curl -sf http://localhost:8000/health | python3 -m json.tool 2>/dev/null || \
	  echo "API non disponible"
