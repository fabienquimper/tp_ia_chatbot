.PHONY: help pull deploy-local deploy-vps deploy-k8s-local deploy-k8s-image \
        k8s-setup k8s-status k8s-logs k8s-destroy status logs stop clean \
        registry-ls test-registry

# ── Variables ─────────────────────────────────────────────────────────────────
include $(wildcard .env)
export

REGISTRY     ?= ghcr.io/fabienquimper
IMAGE_TAG    ?= latest
COMPOSE      := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")
COMPOSE_FILE := docker/docker-compose.prod.yml

help:  ## Affiche cette aide
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(firstword $(MAKEFILE_LIST)) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  REGISTRY=$(REGISTRY)  IMAGE_TAG=$(IMAGE_TAG)"

# ── Registry ──────────────────────────────────────────────────────────────────

test-registry:  ## Teste l'authentification sur ghcr.io
	@if [ -z "$(REGISTRY_TOKEN)" ] || [ -z "$(REGISTRY_USER)" ]; then \
	  echo "REGISTRY_USER / REGISTRY_TOKEN manquants dans .env"; exit 1; \
	fi
	@echo "Test login sur $(REGISTRY) (user: $(REGISTRY_USER))..."
	@echo "$(REGISTRY_TOKEN)" | docker login "$(REGISTRY)" -u "$(REGISTRY_USER)" --password-stdin \
	  && echo "  Login OK" \
	  || echo "  Login ECHEC — vérifier token et droits write:packages"

registry-ls:  ## Liste les versions disponibles sur ghcr.io
	@if [ -z "$(REGISTRY_TOKEN)" ] || [ -z "$(REGISTRY_USER)" ]; then \
	  echo "REGISTRY_USER / REGISTRY_TOKEN manquants dans .env"; exit 1; \
	fi
	@echo "Versions de chatbot-api sur ghcr.io/$(REGISTRY_USER) :"
	@echo ""
	@BODY=$$(curl -s -w "\n%{http_code}" \
	  -H "Authorization: Bearer $(REGISTRY_TOKEN)" \
	  -H "Accept: application/vnd.github+json" \
	  "https://api.github.com/user/packages/container/chatbot-api/versions"); \
	HTTP=$$(echo "$$BODY" | tail -1); \
	JSON=$$(echo "$$BODY" | head -n -1); \
	if [ "$$HTTP" = "404" ]; then \
	  echo "  (aucune image — faire make build-push dans etape_13 d'abord)"; \
	else \
	  echo "$$JSON" | python3 -c "import sys,json; vs=json.load(sys.stdin); [print(f\"  tags={str(v['metadata']['container']['tags']):<30} id={v['id']}  updated={v['updated_at'][:10]}\") for v in vs] if vs else print('  (aucune image)')"; \
	fi

# ── Déploiement Docker Compose depuis GHCR ────────────────────────────────────

pull:  ## Tire l'image depuis ghcr.io sans démarrer
	@echo "$(REGISTRY_TOKEN)" | docker login "$(REGISTRY)" -u "$(REGISTRY_USER)" --password-stdin
	docker pull $(REGISTRY)/chatbot-api:$(IMAGE_TAG)
	@echo ""
	@echo "Image disponible localement : $(REGISTRY)/chatbot-api:$(IMAGE_TAG)"

deploy-local:  ## Lance la stack depuis GHCR en local (sans rebuild)
	@echo "Login sur $(REGISTRY)..."
	@echo "$(REGISTRY_TOKEN)" | docker login "$(REGISTRY)" -u "$(REGISTRY_USER)" --password-stdin
	@echo ""
	@echo "Démarrage de la stack prod locale (image depuis GHCR)..."
	$(COMPOSE) -f $(COMPOSE_FILE) pull
	$(COMPOSE) -f $(COMPOSE_FILE) up -d
	@echo ""
	@echo "Attente du health check..."
	@MAX=60; ELAPSED=0; \
	until curl -sf http://localhost:8000/health > /dev/null 2>&1; do \
	  sleep 2; ELAPSED=$$((ELAPSED + 2)); \
	  if [ $$ELAPSED -ge $$MAX ]; then \
	    echo "Health check timeout — vérifier : $(COMPOSE) -f $(COMPOSE_FILE) logs chatbot"; exit 1; \
	  fi; \
	  printf "."; \
	done; echo ""
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║      Stack prod locale opérationnelle !      ║"
	@echo "╠══════════════════════════════════════════════╣"
	@echo "║  API     : http://localhost:8000/docs        ║"
	@echo "║  Health  : http://localhost:8000/health      ║"
	@echo "║  Metrics : http://localhost:8000/metrics     ║"
	@echo "║  Grafana : http://localhost:3000             ║"
	@echo "╚══════════════════════════════════════════════╝"

deploy-vps:  ## Déploie sur un VPS via SSH (DEPLOY_HOST requis dans .env)
	@if [ -z "$(DEPLOY_HOST)" ]; then \
	  echo "DEPLOY_HOST manquant dans .env (ex: user@monserveur.com)"; exit 1; \
	fi
	@echo "Déploiement vers $(DEPLOY_HOST)..."
	./scripts/deploy-docker.sh --host=$(DEPLOY_HOST) --tag=$(IMAGE_TAG)

# ── Kubernetes local avec kind (Parcours 1 et 2) ──────────────────────────────

k8s-setup:  ## Crée le cluster kind (ports 8080/API 3000/Grafana 9090/Prometheus)
	./scripts/local-cloud.sh setup

deploy-k8s-local:  ## Déploie l'app dans le cluster kind (injecte le .env)
	./scripts/local-cloud.sh deploy
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║    Cluster K8S local opérationnel !          ║"
	@echo "╠══════════════════════════════════════════════╣"
	@echo "║  API       : http://localhost:8080/docs      ║"
	@echo "║  Health    : http://localhost:8080/health    ║"
	@echo "║  Prometheus: http://localhost:9090           ║"
	@echo "║  Grafana   : http://localhost:3000           ║"
	@echo "╚══════════════════════════════════════════════╝"
	@echo "  LLM : $(MODE) — $(LOCAL_BASE_URL)"

deploy-k8s-image:  ## Build l'image locale + charge dans kind + déploie (sans GHCR)
	./scripts/local-cloud.sh deploy-local-image

k8s-status:  ## Statut des pods dans le cluster kind
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║           CLUSTER KIND — OVERVIEW            ║"
	@echo "╚══════════════════════════════════════════════╝"
	@echo ""
	@echo "── Nodes ─────────────────────────────────────"
	@kubectl get nodes -o wide 2>/dev/null || echo "  (cluster non disponible)"
	@echo ""
	@echo "── Pods [chatbot] ────────────────────────────"
	@kubectl get pods -n chatbot -o wide 2>/dev/null || echo "  (namespace chatbot non trouvé)"
	@echo ""
	@echo "── Services [chatbot] ────────────────────────"
	@kubectl get svc -n chatbot 2>/dev/null || true
	@echo ""
	@echo "── Ingress [chatbot] ─────────────────────────"
	@kubectl get ingress -n chatbot 2>/dev/null || true
	@echo ""
	@echo "── Pods [ingress-nginx] ──────────────────────"
	@kubectl get pods -n ingress-nginx 2>/dev/null || true
	@echo ""
	@echo "── Pods [cert-manager] ───────────────────────"
	@kubectl get pods -n cert-manager 2>/dev/null || true
	@echo ""
	@echo "── Health check API ──────────────────────────"
	@curl -sf http://localhost:8080/health | python3 -m json.tool 2>/dev/null || \
	  echo "  API non disponible (normal si deploy-k8s-local pas encore lancé)"
	@echo ""
	@echo "  Grafana    : http://localhost:3000"
	@echo "  Prometheus : http://localhost:9090"
	@echo "  API docs   : http://localhost:8080/docs"

k8s-logs:  ## Logs de l'API dans K8S
	kubectl logs -f deployment/chatbot-api -n chatbot

k8s-destroy:  ## Supprime le cluster kind et tous ses pods
	./scripts/local-cloud.sh destroy

# ── Opérations Docker Compose ─────────────────────────────────────────────────

status:  ## Statut des conteneurs Docker Compose + health check
	$(COMPOSE) -f $(COMPOSE_FILE) ps
	@echo ""
	@curl -sf http://localhost:8000/health | python3 -m json.tool 2>/dev/null || \
	  echo "API non disponible"

logs:  ## Logs de l'API (Docker Compose)
	$(COMPOSE) -f $(COMPOSE_FILE) logs -f chatbot

stop:  ## Arrête la stack Docker Compose
	$(COMPOSE) -f $(COMPOSE_FILE) down

clean:  ## Arrête la stack et supprime les volumes
	$(COMPOSE) -f $(COMPOSE_FILE) down -v
