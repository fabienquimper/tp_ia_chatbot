#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Déploiement Docker Compose sur un VPS / serveur dédié
# Usage : ./scripts/deploy-docker.sh [--host user@server] [--tag v1.2.3]
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Paramètres ────────────────────────────────────────────────────────────────
REMOTE_HOST="${DEPLOY_HOST:-user@your-server.com}"
REMOTE_DIR="${DEPLOY_DIR:-/opt/chatbot}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-ghcr.io/YOUR_ORG}"

for arg in "$@"; do
    case $arg in
        --host=*) REMOTE_HOST="${arg#*=}" ;;
        --tag=*)  IMAGE_TAG="${arg#*=}" ;;
    esac
done

info "Déploiement vers : ${REMOTE_HOST}"
info "Image tag        : ${IMAGE_TAG}"
info "Répertoire remote: ${REMOTE_DIR}"

# ── Transfert des fichiers de configuration ────────────────────────────────────
info "Transfert des fichiers de configuration..."
ssh "${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}/{nginx,grafana/provisioning/{datasources,dashboards}}"

scp etape_13_deployable/docker-compose.prod.yml "${REMOTE_HOST}:${REMOTE_DIR}/"
scp etape_13_deployable/prometheus.yml "${REMOTE_HOST}:${REMOTE_DIR}/"
scp etape_13_deployable/prometheus-alerts.yml "${REMOTE_HOST}:${REMOTE_DIR}/"
scp etape_13_deployable/nginx/nginx.conf "${REMOTE_HOST}:${REMOTE_DIR}/nginx/"
scp -r etape_13_deployable/grafana/ "${REMOTE_HOST}:${REMOTE_DIR}/"

success "Fichiers transférés"

# ── Déploiement sur le serveur ─────────────────────────────────────────────────
info "Déploiement sur le serveur..."

ssh "${REMOTE_HOST}" bash << EOF
set -e
cd ${REMOTE_DIR}

# Login registry
echo "\$GITHUB_TOKEN" | docker login ${REGISTRY%/*} -u \$GITHUB_ACTOR --password-stdin

# Mise à jour de l'image
export IMAGE_TAG=${IMAGE_TAG}
docker compose -f docker-compose.prod.yml pull chatbot

# Rolling update (zero-downtime)
docker compose -f docker-compose.prod.yml up -d --no-build

# Health check
echo "Attente du health check..."
for i in \$(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "Application saine !"
        exit 0
    fi
    sleep 2
done
echo "Health check timeout !"
exit 1
EOF

success "Déploiement réussi !"
info "API disponible sur : https://${REMOTE_HOST#*@}/health"
