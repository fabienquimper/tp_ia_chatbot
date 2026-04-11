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
      - containerPort: 30030
        hostPort: 3000      # Grafana  → http://localhost:3000
        protocol: TCP
      - containerPort: 30090
        hostPort: 9090      # Prometheus → http://localhost:9090
        protocol: TCP
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
    kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=120s
    success "Ingress Controller prêt"

    # Install cert-manager (TLS local)
    info "Installation de cert-manager..."
    # v1.14.x = dernière version compatible avec Kubernetes 1.29
    # (latest utilise selectableFields qui requiert K8s 1.31+)
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.7/cert-manager.yaml
    kubectl rollout status deployment/cert-manager -n cert-manager --timeout=120s
    kubectl rollout status deployment/cert-manager-webhook -n cert-manager --timeout=120s
    success "cert-manager prêt"

    success "Cluster '${CLUSTER_NAME}' opérationnel !"
    info "API sera accessible sur : http://localhost:8080"
}

cmd_deploy() {
    info "Création du namespace..."
    kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || \
        kubectl create namespace "${NAMESPACE}"

    # imagePullSecret pour tirer l'image depuis GHCR (évite docker pull + kind load)
    if [ -n "${REGISTRY_TOKEN:-}" ] && [ -n "${REGISTRY_USER:-}" ]; then
        info "Création du secret GHCR pour pull d'image..."
        kubectl create secret docker-registry ghcr-secret \
            --docker-server=ghcr.io \
            --docker-username="${REGISTRY_USER}" \
            --docker-password="${REGISTRY_TOKEN}" \
            -n "${NAMESPACE}" \
            --dry-run=client -o yaml | kubectl apply -f -
    else
        warning "REGISTRY_USER / REGISTRY_TOKEN absents du .env — l'image doit être publique"
    fi

    # Secrets applicatifs
    kubectl create secret generic chatbot-secrets \
        --from-literal=openai-api-key="${OPENAI_API_KEY:-sk-fake-local-test}" \
        --from-literal=secret-key="local-test-secret-key-32chars-min" \
        --from-literal=grafana-password="admin123" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -

    info "Déploiement des manifests K8S..."
    kubectl apply -k k8s/

    # Injection des variables .env dans le ConfigMap (après apply, sinon écrasé)
    kubectl patch configmap chatbot-config -n "${NAMESPACE}" --type merge \
        -p "{\"data\":{\"MODE\":\"${MODE:-local}\",\"LOCAL_BASE_URL\":\"${LOCAL_BASE_URL:-}\",\"LOCAL_MODEL\":\"${LOCAL_MODEL:-}\"}}"

    # Patches locaux : ingress sans TLS/host + probe timeouts adaptés au LLM lent
    kubectl patch ingress chatbot-ingress -n "${NAMESPACE}" --type=json -p='[
      {"op":"remove","path":"/spec/tls"},
      {"op":"remove","path":"/spec/rules/0/host"},
      {"op":"replace","path":"/metadata/annotations/nginx.ingress.kubernetes.io~1ssl-redirect","value":"false"},
      {"op":"replace","path":"/metadata/annotations/nginx.ingress.kubernetes.io~1force-ssl-redirect","value":"false"}
    ]' 2>/dev/null || true
    kubectl patch deployment chatbot-api -n "${NAMESPACE}" --type=json -p='[
      {"op":"add","path":"/spec/template/spec/containers/0/livenessProbe/timeoutSeconds","value":10},
      {"op":"add","path":"/spec/template/spec/containers/0/readinessProbe/timeoutSeconds","value":10}
    ]' 2>/dev/null || true

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

cmd_deploy_local_image() {
    local build_path="${BUILD_PATH:-../etape_13_deployable}"

    # 1. Build l'image locale
    info "Build de l'image locale depuis '${build_path}'..."
    docker build -t chatbot-api:local "${build_path}"
    success "Image chatbot-api:local créée"
    echo ""

    # 2. Charger l'image dans le cluster kind (le cluster ne voit pas le daemon Docker local)
    info "Chargement de l'image dans le cluster kind '${CLUSTER_NAME}'..."
    kind load docker-image chatbot-api:local --name "${CLUSTER_NAME}"
    success "Image disponible dans le cluster"
    echo ""

    # 3. Namespace
    info "Création du namespace '${NAMESPACE}'..."
    kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1 || \
        kubectl create namespace "${NAMESPACE}"

    # 4. Secrets applicatifs (exclus des manifests Git — données sensibles)
    info "Création des secrets applicatifs..."
    kubectl create secret generic chatbot-secrets \
        --from-literal=openai-api-key="${OPENAI_API_KEY:-sk-fake-local-test}" \
        --from-literal=secret-key="local-test-secret-key-32chars-min" \
        --from-literal=grafana-password="admin123" \
        -n "${NAMESPACE}" \
        --dry-run=client -o yaml | kubectl apply -f -

    # 5. Déploiement via l'overlay kustomize (image locale, imagePullPolicy Never)
    info "Déploiement des manifests (overlay image locale)..."
    kubectl apply -k k8s/overlays/local-image/

    # Injection des variables .env dans le ConfigMap (après apply, sinon écrasé)
    kubectl patch configmap chatbot-config -n "${NAMESPACE}" --type merge \
        -p "{\"data\":{\"MODE\":\"${MODE:-local}\",\"LOCAL_BASE_URL\":\"${LOCAL_BASE_URL:-}\",\"LOCAL_MODEL\":\"${LOCAL_MODEL:-}\"}}"
    echo ""

    # 6. Attente
    info "Attente que les pods soient Running..."
    kubectl rollout status deployment/chatbot-api -n "${NAMESPACE}" --timeout=3m
    echo ""

    success "Application déployée depuis l'image locale !"
    echo ""
    kubectl get pods -n "${NAMESPACE}"
    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║   Cluster K8S (image locale) opérationnel !   ║"
    echo "╠════════════════════════════════════════════════╣"
    echo "║  API       : http://localhost:8080/docs        ║"
    echo "║  Health    : http://localhost:8080/health      ║"
    echo "║  Prometheus: http://localhost:9090             ║"
    echo "║  Grafana   : http://localhost:3000             ║"
    echo "╚════════════════════════════════════════════════╝"
}

cmd_destroy() {
    warning "Suppression du cluster '${CLUSTER_NAME}'..."
    kind delete cluster --name "${CLUSTER_NAME}"
    success "Cluster supprimé"
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case "${1:-help}" in
    setup)              cmd_setup ;;
    deploy)             cmd_deploy ;;
    deploy-local-image) cmd_deploy_local_image ;;
    status)             cmd_status ;;
    destroy)            cmd_destroy ;;
    *)
        echo "Usage : $0 {setup|deploy|deploy-local-image|status|destroy}"
        echo ""
        echo "  setup               — Crée le cluster kind local"
        echo "  deploy              — Déploie depuis GHCR (nécessite REGISTRY_TOKEN)"
        echo "  deploy-local-image  — Build + charge l'image locale, déploie sans GHCR"
        echo "  status              — Affiche le statut"
        echo "  destroy             — Supprime le cluster"
        ;;
esac
