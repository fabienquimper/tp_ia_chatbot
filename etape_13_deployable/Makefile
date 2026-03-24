.PHONY: help dev prod test build clean index-rag index-rag-docker index-rag-paragraph index-rag-section logs stop eval eval-strict eval-verbose smoke smoke-no-rag

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
	$(COMPOSE) down --remove-orphans 2>/dev/null || true
	$(COMPOSE) up --build

dev-bg:  ## Lance en arrière-plan (supprime l'ancien conteneur d'abord)
	$(COMPOSE) down --remove-orphans 2>/dev/null || true
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
eval:  ## Évaluation complète : 15 questions (exit 0 si score ≥ 70%)
	python scripts/eval.py --eval-file data/eval_set.jsonl --pass-threshold 70

eval-strict:  ## Évaluation stricte pour CI : exit 1 si le moindre FAIL
	python scripts/eval.py --eval-file data/eval_set.jsonl --pass-threshold 100

eval-verbose:  ## Évaluation complète avec réponses complètes affichées
	python scripts/eval.py --eval-file data/eval_set.jsonl --verbose --pass-threshold 70

smoke:  ## Smoke test : 5 questions rapides pour vérifier que l'API répond
	python scripts/eval.py --eval-file data/eval_set.jsonl --count 5 --shuffle --pass-threshold 60

smoke-no-rag:  ## Smoke test sans RAG
	python scripts/eval.py --eval-file data/eval_set.jsonl --count 5 --no-rag --pass-threshold 60

# ── RAG ───────────────────────────────────────────────────────────────────────
index-rag:  ## Indexe les documents (méthode définie dans index_rag.py)
	python scripts/index_rag.py

index-rag-paragraph:  ## Indexe avec la méthode paragraphes (classique)
	python scripts/index_rag.py --method paragraph

index-rag-section:  ## Indexe avec la méthode sections (recommandée, meilleure précision)
	python scripts/index_rag.py --method section

index-rag-docker:  ## Indexe dans le conteneur Docker (méthode définie dans index_rag.py)
	$(COMPOSE) exec chatbot python scripts/index_rag.py --docs-dir docs

index-rag-docker-paragraph:  ## Indexe dans Docker, méthode paragraphes
	$(COMPOSE) exec chatbot python scripts/index_rag.py --docs-dir docs --method paragraph

index-rag-docker-section:  ## Indexe dans Docker, méthode sections
	$(COMPOSE) exec chatbot python scripts/index_rag.py --docs-dir docs --method section

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
