.PHONY: help dev prod test build build-push build-skip-tests clean images test-registry registry-ls registry-rm index-rag index-rag-docker index-rag-paragraph index-rag-section logs stop eval eval-strict eval-verbose smoke smoke-no-rag

# Variables
IMAGE  := chatbot-api
TAG    := $(shell git rev-parse --short HEAD 2>/dev/null || echo latest)
COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | \
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

build-push:  ## Construit et pousse vers le registry (REGISTRY=ghcr.io/org requis)
	./build.sh --push

test-registry:  ## Teste l'authentification sur le registry (sans build ni push)
	@. ./.env 2>/dev/null || true; \
	if [ -z "$$REGISTRY" ]; then echo "REGISTRY non défini dans .env"; exit 1; fi; \
	if [ -z "$$REGISTRY_TOKEN" ] || [ -z "$$REGISTRY_USER" ]; then echo "REGISTRY_USER / REGISTRY_TOKEN manquants dans .env"; exit 1; fi; \
	echo "Test login sur $$REGISTRY (user: $$REGISTRY_USER)..."; \
	echo "$$REGISTRY_TOKEN" | docker login "$$REGISTRY" -u "$$REGISTRY_USER" --password-stdin \
	  && echo "  Login OK — push autorisé" \
	  || echo "  Login ECHEC — vérifier token et droits write:packages"

registry-ls:  ## Liste les versions et tags disponibles sur ghcr.io pour chatbot-api
	@. ./.env 2>/dev/null || true; \
	if [ -z "$$REGISTRY_TOKEN" ] || [ -z "$$REGISTRY_USER" ]; then \
	  echo "REGISTRY_USER / REGISTRY_TOKEN manquants dans .env"; exit 1; \
	fi; \
	echo "Versions de chatbot-api sur ghcr.io/$$REGISTRY_USER :"; \
	echo ""; \
	BODY=$$(curl -s -w "\n%{http_code}" \
	  -H "Authorization: Bearer $$REGISTRY_TOKEN" \
	  -H "Accept: application/vnd.github+json" \
	  "https://api.github.com/user/packages/container/chatbot-api/versions"); \
	HTTP=$$(echo "$$BODY" | tail -1); \
	JSON=$$(echo "$$BODY" | head -n -1); \
	if [ "$$HTTP" = "404" ]; then \
	  echo "  (aucune image — faire make build-push d'abord)"; \
	else \
	  echo "$$JSON" | python3 -c "import sys,json; vs=json.load(sys.stdin); [print(f\"  tags={str(v['metadata']['container']['tags']):<30} id={v['id']}  updated={v['updated_at'][:10]}\") for v in vs] if vs else print('  (aucune image)')"; \
	fi

registry-rm:  ## Supprime un tag distant sur ghcr.io (TAG=sha1234 requis)
	@. ./.env 2>/dev/null || true; \
	if [ -z "$$REGISTRY_TOKEN" ] || [ -z "$$REGISTRY_USER" ]; then \
	  echo "REGISTRY_USER / REGISTRY_TOKEN manquants dans .env"; exit 1; \
	fi; \
	if [ -z "$(TAG)" ]; then \
	  echo "Usage : make registry-rm TAG=<tag>   ex: make registry-rm TAG=b5b88ec"; exit 1; \
	fi; \
	echo "Recherche du tag '$(TAG)' dans chatbot-api sur ghcr.io..."; \
	VERSION_ID=$$(curl -sf \
	  -H "Authorization: Bearer $$REGISTRY_TOKEN" \
	  -H "Accept: application/vnd.github+json" \
	  "https://api.github.com/user/packages/container/chatbot-api/versions" \
	| python3 -c "import sys,json; vs=json.load(sys.stdin); m=[v for v in vs if '$(TAG)' in v.get('metadata',{}).get('container',{}).get('tags',[])]; print(m[0]['id'] if m else '')"); \
	if [ -z "$$VERSION_ID" ]; then \
	  echo "Tag '$(TAG)' introuvable sur ghcr.io"; exit 1; \
	fi; \
	echo "Suppression version id=$$VERSION_ID (tag: $(TAG))..."; \
	HTTP_CODE=$$(curl -s -o /tmp/registry_rm_response.json -w "%{http_code}" -X DELETE \
	  -H "Authorization: Bearer $$REGISTRY_TOKEN" \
	  -H "Accept: application/vnd.github+json" \
	  "https://api.github.com/user/packages/container/chatbot-api/versions/$$VERSION_ID"); \
	if [ "$$HTTP_CODE" = "204" ]; then \
	  echo "  Tag '$(TAG)' supprimé"; \
	elif grep -q "last tagged version" /tmp/registry_rm_response.json 2>/dev/null; then \
	  echo "  Dernière version — suppression du package entier chatbot-api..."; \
	  HTTP2=$$(curl -s -o /tmp/registry_rm2.json -w "%{http_code}" -X DELETE \
	    -H "Authorization: Bearer $$REGISTRY_TOKEN" \
	    -H "Accept: application/vnd.github+json" \
	    "https://api.github.com/user/packages/container/chatbot-api"); \
	  if [ "$$HTTP2" = "204" ]; then \
	    echo "  Package chatbot-api supprimé entièrement"; \
	  else \
	    echo "  Echec HTTP $$HTTP2 :"; cat /tmp/registry_rm2.json; echo ""; \
	  fi; \
	else \
	  echo "  Echec HTTP $$HTTP_CODE :"; cat /tmp/registry_rm_response.json; echo ""; \
	fi

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

images:  ## Liste les images Docker buildées pour ce projet
	@echo "Images locales (chatbot-api) :"
	@docker images $(IMAGE) --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedSince}}"
	@echo ""
	@echo "Pour voir toutes les images Docker : docker images"
