#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Déploiement Kubernetes
# Usage : ./scripts/deploy-k8s.sh [--tag v1.2.3] [--namespace chatbot]
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Paramètres ────────────────────────────────────────────────────────────────
NAMESPACE="${NAMESPACE:-chatbot}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-ghcr.io/YOUR_ORG}"
K8S_DIR="etape_14_deployed/k8s"
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --tag=*)       IMAGE_TAG="${arg#*=}" ;;
        --namespace=*) NAMESPACE="${arg#*=}" ;;
        --dry-run)     DRY_RUN=true ;;
    esac
done

# ── Vérifications ─────────────────────────────────────────────────────────────
command -v kubectl >/dev/null 2>&1 || error "kubectl non installé"
kubectl cluster-info >/dev/null 2>&1 || error "Pas de connexion au cluster Kubernetes"

info "Cluster     : $(kubectl config current-context)"
info "Namespace   : ${NAMESPACE}"
info "Image tag   : ${IMAGE_TAG}"
info "Dry run     : ${DRY_RUN}"

# ── Dry run ───────────────────────────────────────────────────────────────────
if [ "$DRY_RUN" = true ]; then
    info "Mode dry-run : validation des manifests"
    kubectl apply -k "${K8S_DIR}/" --dry-run=client
    success "Manifests valides"
    exit 0
fi

# ── Déploiement ───────────────────────────────────────────────────────────────
info "Étape 1/4 : Création du namespace"
kubectl apply -f "${K8S_DIR}/namespace.yaml"

info "Étape 2/4 : Mise à jour de l'image"
# Met à jour le tag dans kustomization.yaml
sed -i "s/newTag:.*/newTag: ${IMAGE_TAG}/" "${K8S_DIR}/kustomization.yaml"

info "Étape 3/4 : Application des manifests"
kubectl apply -k "${K8S_DIR}/"

info "Étape 4/4 : Attente du rollout"
kubectl rollout status deployment/chatbot-api -n "${NAMESPACE}" --timeout=5m

# ── Health check ───────────────────────────────────────────────────────────────
info "Vérification du health check..."
POD=$(kubectl get pods -n "${NAMESPACE}" -l app=chatbot-api \
      -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -n "$POD" ]; then
    kubectl exec -n "${NAMESPACE}" "${POD}" -- \
        curl -sf http://localhost:8000/health
    success "Pod ${POD} : sain"
fi

success "Déploiement K8S terminé !"
echo ""
kubectl get pods -n "${NAMESPACE}"
echo ""
kubectl get services -n "${NAMESPACE}"
