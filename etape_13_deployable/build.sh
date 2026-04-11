#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Étape 13 — Script de Build & Déploiement
# Usage : ./build.sh [--skip-tests] [--push] [--env prod|dev]
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Couleurs ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Chargement du .env (les variables déjà exportées dans l'env ont priorité) ─
if [ -f ".env" ]; then
    set -o allexport
    # shellcheck disable=SC1091
    source .env
    set +o allexport
fi

# ── Paramètres ────────────────────────────────────────────────────────────────
SKIP_TESTS=false
PUSH_IMAGE=false
ENV="dev"
IMAGE_NAME="${IMAGE_NAME:-chatbot-api}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
REGISTRY="${REGISTRY:-}"
COMPOSE=$(docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

for arg in "$@"; do
    case $arg in
        --skip-tests) SKIP_TESTS=true ;;
        --push)       PUSH_IMAGE=true ;;
        --env=*)      ENV="${arg#*=}" ;;
    esac
done

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Build Pipeline — Étape 13 (deployable)    ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
info "Image    : ${IMAGE_NAME}:${IMAGE_TAG}"
info "Env      : ${ENV}"
info "Tests    : $([ "$SKIP_TESTS" = true ] && echo 'skipped' || echo 'enabled')"
echo ""

# ── 1. Vérifications pré-build ────────────────────────────────────────────────
info "Étape 1/5 : Vérifications pré-build"

command -v docker >/dev/null 2>&1 || error "Docker non installé"
command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1 || \
    docker-compose version >/dev/null 2>&1 || error "Docker Compose non installé"

if [ ! -f ".env" ] && [ "$ENV" = "prod" ]; then
    error "Fichier .env manquant en mode prod. Copier .env.example → .env et remplir les valeurs."
fi
success "Pré-vérifications OK"

# ── 2. Tests ──────────────────────────────────────────────────────────────────
if [ "$SKIP_TESTS" = false ]; then
    info "Étape 2/5 : Exécution des tests (dans Docker)"

    docker build --target test -t "${IMAGE_NAME}:test" . \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        2>&1 | tee /tmp/test_output.log

    TEST_EXIT=${PIPESTATUS[0]}
    if [ $TEST_EXIT -ne 0 ]; then
        error "Tests échoués ! Déploiement annulé. Voir /tmp/test_output.log"
    fi
    success "Tous les tests passent ✓"
else
    warning "Tests ignorés (--skip-tests)"
fi

# ── 3. Build de l'image de production ─────────────────────────────────────────
info "Étape 3/5 : Build image production"

docker build \
    --target production \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    -t "${IMAGE_NAME}:latest" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

success "Image construite : ${IMAGE_NAME}:${IMAGE_TAG}"

# ── 4. Push vers le registry (optionnel) ──────────────────────────────────────
if [ "$PUSH_IMAGE" = true ]; then
    info "Étape 4/5 : Push vers le registry"

    if [ -n "$REGISTRY" ]; then
        # Authentification si les variables sont disponibles
        if [ -n "${REGISTRY_TOKEN:-}" ] && [ -n "${REGISTRY_USER:-}" ]; then
            info "Authentification sur ${REGISTRY}..."
            echo "$REGISTRY_TOKEN" | docker login "$REGISTRY" -u "$REGISTRY_USER" --password-stdin \
                || error "Échec de l'authentification sur ${REGISTRY}"
            success "Connecté à ${REGISTRY}"
        else
            warning "REGISTRY_USER / REGISTRY_TOKEN non définis — login ignoré (supposé déjà connecté)"
        fi

        FULL_TAG="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$FULL_TAG"
        docker push "$FULL_TAG"
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY}/${IMAGE_NAME}:latest"
        docker push "${REGISTRY}/${IMAGE_NAME}:latest"
        success "Image poussée : ${FULL_TAG}"
    else
        warning "REGISTRY non défini — push ignoré"
    fi
else
    info "Étape 4/5 : Push ignoré (utiliser --push pour activer)"
fi

# ── 5. Déploiement local ──────────────────────────────────────────────────────
info "Étape 5/5 : Déploiement Docker Compose"

COMPOSE_FILE="docker-compose.yml"
if [ "$ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

$COMPOSE down --remove-orphans 2>/dev/null || true
$COMPOSE -f "$COMPOSE_FILE" up -d --build

# Attente health check
info "En attente du health check..."
MAX_WAIT=60
ELAPSED=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        error "Health check timeout après ${MAX_WAIT}s. Vérifier : docker compose logs chatbot"
    fi
    echo -n "."
done
echo ""

success "Application démarrée et saine !"
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║             Déploiement réussi !             ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  API     : http://localhost:8000/docs        ║"
echo "║  Health  : http://localhost:8000/health      ║"
echo "║  Metrics : http://localhost:8000/metrics     ║"
echo "║  Grafana : http://localhost:3000             ║"
echo "║  Prometheus: http://localhost:9090           ║"
echo "╚══════════════════════════════════════════════╝"
