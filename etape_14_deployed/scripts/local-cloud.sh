#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Cloud local avec kind (Kubernetes IN Docker)
# Simule un cluster K8S complet sur votre machine.
#
# Usage :
#   ./scripts/local-cloud.sh setup    # Crée le cluster
#   ./scripts/local-cloud.sh deploy   # Déploie l'app
#   ./scripts/local-cloud.sh status   # Statut
#   ./scripts/local-cloud.sh destroy  # Supprime le cluster
#
# Prérequis : Docker, kind, kubectl
#   brew install kind kubectl (macOS)
#   choco install kind kubernetes-cli (Windows)
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

CLUSTER_NAME="chatbot-local"
NAMESPACE="chatbot"
IMAGE="chatbot-api:local"

# ── Configuration du cluster kind ─────────────────────────────────────────────
KIND_CONFIG=$(cat <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: chatbot-local
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 8080      # API via Ingress sur http://localhost:8080
        protocol: TCP
      - containerPort: 443
        hostPort: 8443      # HTTPS local
        protocol: TCP
  - role: worker
  - role: worker
EOF
)

# ── Commandes ─────────────────────────────────────────────────────────────────

cmd_setup() {
    info "Création du cluster kind '${CLUSTER_NAME}'..."
    command -v kind >/dev/null 2>&1 || error "kind non installé. Voir https://kind.sigs.k8s.io/docs/user/quick-start/"
    command -v kubectl >/dev/null 2>&1 || error "kubectl non installé."

    # Crée le cluster
    echo "${KIND_CONFIG}" | kind create cluster --config=-
    success "Cluster créé"

    # Install Nginx Ingress Controller (adapté pour kind)
    info "Installation de Nginx Ingress Controller..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=120s
    success "Ingress Controller prêt"

    # Install cert-manager (TLS local)
    info "Installation de cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
    kubectl wait --namespace cert-manager \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/instance=cert-manager \
        --timeout=120s
    success "cert-manager prêt"

    success "Cluster '${CLUSTER_NAME}' opérationnel !"
    info "API sera accessible sur : http://localhost:8080"
}

cmd_deploy() {
    info "Build de l'image locale..."
    docker build --target production -t "${IMAGE}" etape_13_deployable/

    info "Chargement de l'image dans kind..."
    kind load docker-image "${IMAGE}" --name "${CLUSTER_NAME}"

    info "Création du namespace et du secret de base..."
    kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || \
        kubectl create namespace "${NAMESPACE}"

    # Secret minimal pour le test local
    kubectl create secret generic chatbot-secrets \
        --from-literal=openai-api-key="${OPENAI_API_KEY:-sk-fake-local-test}" \
        --from-literal=secret-key="local-test-secret-key-32chars-min" \
        --from-literal=grafana-password="admin123" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -

    info "Déploiement des manifests K8S..."
    kubectl apply -k etape_14_deployed/k8s/

    info "Mise à jour de l'image vers la version locale..."
    kubectl set image deployment/chatbot-api \
        chatbot="${IMAGE}" \
        -n "${NAMESPACE}"

    info "Attente du déploiement..."
    kubectl rollout status deployment/chatbot-api -n "${NAMESPACE}" --timeout=3m

    success "Application déployée !"
    echo ""
    kubectl get pods -n "${NAMESPACE}"
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║  Cloud local opérationnel !               ║"
    echo "╠════════════════════════════════════════════╣"
    echo "║  API   : http://localhost:8080/docs        ║"
    echo "║  Health: http://localhost:8080/health      ║"
    echo "╚════════════════════════════════════════════╝"
}

cmd_status() {
    info "Statut du cluster '${CLUSTER_NAME}'"
    kubectl get nodes
    echo ""
    kubectl get pods -n "${NAMESPACE}" -o wide 2>/dev/null || \
        warning "Namespace '${NAMESPACE}' non trouvé"
    echo ""
    kubectl get services -n "${NAMESPACE}" 2>/dev/null || true
    echo ""
    kubectl get ingress -n "${NAMESPACE}" 2>/dev/null || true
}

cmd_destroy() {
    warning "Suppression du cluster '${CLUSTER_NAME}'..."
    kind delete cluster --name "${CLUSTER_NAME}"
    success "Cluster supprimé"
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case "${1:-help}" in
    setup)   cmd_setup ;;
    deploy)  cmd_deploy ;;
    status)  cmd_status ;;
    destroy) cmd_destroy ;;
    *)
        echo "Usage : $0 {setup|deploy|status|destroy}"
        echo ""
        echo "  setup    — Crée le cluster kind local"
        echo "  deploy   — Build et déploie l'application"
        echo "  status   — Affiche le statut"
        echo "  destroy  — Supprime le cluster"
        ;;
esac
