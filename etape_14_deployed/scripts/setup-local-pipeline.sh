#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# Pipeline CI/CD local — registry + Gitea + kind + ArgoCD
#
# Simule un pipeline de production complet sans compte cloud :
#   • Registry Docker local      → port 5001
#   • Gitea (Git server local)   → port 3001 (UI) / 2222 (SSH)
#   • kind (K8S local)           → port 8080 (API) / 8443 (HTTPS)
#   • ArgoCD (GitOps)            → port 8081 (UI)
#
# Usage :
#   ./scripts/setup-local-pipeline.sh setup      # Installation complète
#   ./scripts/setup-local-pipeline.sh ci         # Lance le CI avec act
#   ./scripts/setup-local-pipeline.sh push-image # Build + push vers registry local
#   ./scripts/setup-local-pipeline.sh sync       # Déclenche la sync ArgoCD
#   ./scripts/setup-local-pipeline.sh status     # Statut de tous les composants
#   ./scripts/setup-local-pipeline.sh destroy    # Supprime tout
#
# Prérequis : Docker, kind, kubectl, act, argocd (CLI optionnel)
#   Linux    : voir docs/LOCAL_PIPELINE.md pour l'installation
#   macOS    : brew install kind kubectl act argocd
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warning() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
step()    { echo -e "\n${CYAN}══ $* ══${NC}"; }

# ── Configuration ─────────────────────────────────────────────────────────────
CLUSTER_NAME="chatbot-pipeline"
NAMESPACE="chatbot"
REGISTRY_NAME="local-registry"
REGISTRY_PORT="5001"
GITEA_NAME="local-gitea"
GITEA_PORT="3001"
GITEA_SSH_PORT="2222"
ARGOCD_NAMESPACE="argocd"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── Vérification des prérequis ────────────────────────────────────────────────
check_prereqs() {
    local missing=()
    command -v docker  >/dev/null 2>&1 || missing+=("docker")
    command -v kind    >/dev/null 2>&1 || missing+=("kind")
    command -v kubectl >/dev/null 2>&1 || missing+=("kubectl")

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Prérequis manquants : ${missing[*]}\nVoir docs/LOCAL_PIPELINE.md pour l'installation."
    fi
    success "Prérequis OK"
}

# ── Registry Docker local ──────────────────────────────────────────────────────
setup_registry() {
    step "Registry Docker local (localhost:${REGISTRY_PORT})"

    if docker inspect "${REGISTRY_NAME}" >/dev/null 2>&1; then
        warning "Registry '${REGISTRY_NAME}' déjà en cours d'exécution"
        return
    fi

    docker run -d \
        --name "${REGISTRY_NAME}" \
        --restart=unless-stopped \
        -p "${REGISTRY_PORT}:5000" \
        registry:2

    success "Registry démarré → localhost:${REGISTRY_PORT}"
}

# ── Gitea (serveur Git local) ──────────────────────────────────────────────────
setup_gitea() {
    step "Gitea — serveur Git local (localhost:${GITEA_PORT})"

    if docker inspect "${GITEA_NAME}" >/dev/null 2>&1; then
        warning "Gitea '${GITEA_NAME}' déjà en cours d'exécution"
        return
    fi

    docker volume create gitea-data >/dev/null

    docker run -d \
        --name "${GITEA_NAME}" \
        --restart=unless-stopped \
        -p "${GITEA_PORT}:3000" \
        -p "${GITEA_SSH_PORT}:22" \
        -v gitea-data:/data \
        -e GITEA__server__ROOT_URL="http://localhost:${GITEA_PORT}" \
        -e GITEA__server__HTTP_PORT="3000" \
        -e GITEA__database__DB_TYPE="sqlite3" \
        -e GITEA__database__PATH="/data/gitea/gitea.db" \
        -e GITEA__security__INSTALL_LOCK="true" \
        gitea/gitea:latest

    info "Gitea en cours de démarrage..."
    sleep 8

    # Créer le compte admin automatiquement via CLI (évite le wizard web)
    if docker exec -u git "${GITEA_NAME}" gitea admin user create \
            --username admin \
            --password admin1234 \
            --email admin@local.dev \
            --admin 2>/dev/null; then
        success "Gitea prêt → http://localhost:${GITEA_PORT}"
        echo "  Login : admin / admin1234"
        echo ""
        echo "  Créer un repo 'chatbot-api' puis pousser le code :"
        echo "    git remote add local http://localhost:${GITEA_PORT}/admin/chatbot-api.git"
        echo "    git push local main"
    else
        warning "Gitea démarre encore ou compte admin déjà existant"
        info "Accès : http://localhost:${GITEA_PORT}  (admin / admin1234)"
    fi
}

# ── Cluster kind avec registry ─────────────────────────────────────────────────
setup_kind() {
    step "Cluster kind '${CLUSTER_NAME}' avec registry locale"

    # Pré-créer le réseau Docker 'kind' sans IPv6 (évite l'erreur ip6tables sur certains kernels)
    if ! docker network inspect kind >/dev/null 2>&1; then
        docker network create -d=bridge \
            -o com.docker.network.bridge.enable_ip_masquerade=true \
            -o com.docker.network.driver.mtu=1500 \
            kind
        success "Réseau Docker 'kind' créé (IPv4 uniquement)"
    fi

    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        warning "Cluster '${CLUSTER_NAME}' déjà existant"
    else
        # Config kind : 1 control-plane + 2 workers + ports exposés + registry locale
        cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER_NAME}
# Forcer IPv4 uniquement (évite les problèmes ip6tables sur certains kernels Linux)
networking:
  ipFamily: ipv4
# Connexion au registry local (localhost:${REGISTRY_PORT})
containerdConfigPatches:
  - |-
    [plugins."io.containerd.grpc.v1.cri".registry]
      config_path = ""
      [plugins."io.containerd.grpc.v1.cri".registry.mirrors]
        [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:${REGISTRY_PORT}"]
          endpoint = ["http://${REGISTRY_NAME}:5000"]
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
        hostPort: 8080
        protocol: TCP
      - containerPort: 443
        hostPort: 8443
        protocol: TCP
  - role: worker
  - role: worker
EOF
        success "Cluster créé"
    fi

    # Connecter le registry au réseau kind
    if ! docker network inspect kind | grep -q "${REGISTRY_NAME}"; then
        docker network connect kind "${REGISTRY_NAME}" 2>/dev/null || true
        success "Registry connecté au réseau kind"
    fi

    # ConfigMap pour que kind connaisse le registry (convention standard)
    kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: local-registry-hosting
  namespace: kube-public
data:
  localRegistryHosting.v1: |
    host: "localhost:${REGISTRY_PORT}"
    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"
EOF

    # Nginx Ingress Controller
    info "Installation Nginx Ingress Controller..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=120s
    success "Ingress Controller prêt"
}

# ── ArgoCD ────────────────────────────────────────────────────────────────────
setup_argocd() {
    step "ArgoCD — GitOps controller"

    # Installation
    kubectl get namespace "${ARGOCD_NAMESPACE}" >/dev/null 2>&1 || \
        kubectl create namespace "${ARGOCD_NAMESPACE}"

    # --server-side : obligatoire pour ArgoCD — les CRDs dépassent la limite de 262 Ko
    # des annotations last-applied-configuration gérées côté client (kubectl apply classique)
    kubectl apply -n "${ARGOCD_NAMESPACE}" \
        --server-side \
        -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

    info "Attente qu'ArgoCD soit prêt (peut prendre 2-3 min)..."
    kubectl wait --namespace "${ARGOCD_NAMESPACE}" \
        --for=condition=available deployment/argocd-server \
        --timeout=300s

    # Récupérer le mot de passe admin initial
    ARGOCD_PASSWORD=$(kubectl -n "${ARGOCD_NAMESPACE}" get secret argocd-initial-admin-secret \
        -o jsonpath="{.data.password}" | base64 -d 2>/dev/null || echo "(non disponible)")

    success "ArgoCD prêt"
    echo ""
    echo "  Accès ArgoCD (via port-forward) :"
    echo "    kubectl port-forward svc/argocd-server -n argocd 8081:443 &"
    echo "    https://localhost:8081"
    echo "    Login : admin / ${ARGOCD_PASSWORD}"
    echo ""

    # Appliquer l'Application ArgoCD si Gitea est configuré
    ARGOCD_APP="${PROJECT_ROOT}/k8s/argocd/application.yaml"
    if [[ -f "${ARGOCD_APP}" ]]; then
        info "Application ArgoCD disponible — à appliquer après avoir configuré Gitea :"
        echo "    kubectl apply -f k8s/argocd/application.yaml"
    fi
}

# ── Configuration act ─────────────────────────────────────────────────────────
setup_act() {
    step "Configuration de act (GitHub Actions local)"

    ACTRC="${PROJECT_ROOT}/../.actrc"  # à la racine du projet git
    if [[ ! -f "${ACTRC}" ]]; then
        cat > "${ACTRC}" <<EOF
# act — Configuration pour CI/CD local
# Utilise l'image Ubuntu complète pour compatibilité maximale
-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
-P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04

# Fichier de secrets locaux (ne pas committer)
--secret-file .secrets.act
EOF
        success "Créé : .actrc (racine du repo)"
    else
        warning ".actrc déjà existant"
    fi

    # Template du fichier de secrets
    SECRETS_TEMPLATE="${PROJECT_ROOT}/../.secrets.act.example"
    if [[ ! -f "${SECRETS_TEMPLATE}" ]]; then
        cat > "${SECRETS_TEMPLATE}" <<EOF
# Copier en .secrets.act et remplir les valeurs
# Ne jamais committer .secrets.act

# Clé API (utilisée par les tests et le build)
OPENAI_API_KEY=sk-fake-for-local-ci

# Registry local (remplace GHCR en local)
REGISTRY=localhost:${REGISTRY_PORT}

# Pour le push vers le registry local
GITHUB_TOKEN=local-token-not-needed-for-local-registry
EOF
        success "Créé : .secrets.act.example (racine du repo)"
        info "Copier en .secrets.act et adapter les valeurs"
    fi

    if command -v act >/dev/null 2>&1; then
        success "act installé : $(act --version)"
    else
        warning "act non installé. Installation :"
        echo "  Linux  : curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
        echo "  macOS  : brew install act"
    fi
}

# ── CI local avec act ──────────────────────────────────────────────────────────
cmd_ci() {
    command -v act >/dev/null 2>&1 || error "act non installé. Voir docs/LOCAL_PIPELINE.md"

    step "CI local avec act"
    info "Exécution du workflow ci.yml en local..."

    cd "${PROJECT_ROOT}/.."  # Racine du repo git

    # Lance uniquement les jobs lint et tests (les plus utiles en local)
    # --job : filtre un job spécifique ; omettre pour tout lancer
    act push \
        --secret-file .secrets.act \
        --workflows etape_14_deployed/.github/workflows/ci.yml \
        --platform ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest \
        "$@"
}

# ── Build et push vers le registry local ──────────────────────────────────────
cmd_push_image() {
    step "Build et push image → localhost:${REGISTRY_PORT}"

    local tag="${IMAGE_TAG:-latest}"
    local image="localhost:${REGISTRY_PORT}/chatbot-api:${tag}"

    info "Build : ${image}"
    docker build --target production \
        -t "${image}" \
        "${PROJECT_ROOT}/../etape_13_deployable/"

    info "Push → registry local..."
    docker push "${image}"

    success "Image disponible : ${image}"
    info "Pour déployer dans kind : adapter chatbot-deployment.yaml avec cette image"
}

# ── Sync ArgoCD ───────────────────────────────────────────────────────────────
cmd_sync() {
    step "Sync ArgoCD"

    if command -v argocd >/dev/null 2>&1; then
        argocd app sync chatbot-api --force
    else
        kubectl -n "${ARGOCD_NAMESPACE}" rollout restart deployment/argocd-application-controller
        info "argocd CLI non installé — relance du controller pour forcer la sync"
        info "Ou via UI : https://localhost:8081 → chatbot-api → Sync"
    fi
}

# ── Statut ────────────────────────────────────────────────────────────────────
cmd_status() {
    step "Statut du pipeline local"

    echo -e "\n${CYAN}Registry (localhost:${REGISTRY_PORT})${NC}"
    docker inspect "${REGISTRY_NAME}" --format '  Status: {{.State.Status}}' 2>/dev/null || \
        echo "  Non démarré"
    curl -sf "http://localhost:${REGISTRY_PORT}/v2/_catalog" 2>/dev/null | \
        python3 -c "import sys,json; repos=json.load(sys.stdin).get('repositories',[]); print(f'  Images: {repos if repos else \"(vide)\"}')" 2>/dev/null || \
        echo "  (registry non accessible)"

    echo -e "\n${CYAN}Gitea (localhost:${GITEA_PORT})${NC}"
    docker inspect "${GITEA_NAME}" --format '  Status: {{.State.Status}}' 2>/dev/null || \
        echo "  Non démarré"

    echo -e "\n${CYAN}Cluster kind${NC}"
    kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$" && \
        kubectl get nodes --no-headers 2>/dev/null || \
        echo "  Non créé"

    echo -e "\n${CYAN}Pods chatbot${NC}"
    kubectl get pods -n "${NAMESPACE}" 2>/dev/null || \
        echo "  Namespace '${NAMESPACE}' non trouvé"

    echo -e "\n${CYAN}ArgoCD${NC}"
    kubectl get pods -n "${ARGOCD_NAMESPACE}" --no-headers 2>/dev/null | \
        awk '{print "  " $1 " — " $3}' || \
        echo "  Non installé"

    echo ""
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║  URLs d'accès                                         ║"
    echo "╠═══════════════════════════════════════════════════════╣"
    echo "║  API chatbot  : http://localhost:8080/docs            ║"
    echo "║  Gitea        : http://localhost:${GITEA_PORT}                   ║"
    echo "║  ArgoCD       : https://localhost:8081 (port-forward) ║"
    echo "║  Registry     : http://localhost:${REGISTRY_PORT}                ║"
    echo "╚═══════════════════════════════════════════════════════╝"
}

# ── Destroy ───────────────────────────────────────────────────────────────────
cmd_destroy() {
    warning "Suppression de tous les composants du pipeline local..."
    read -rp "Confirmer ? [y/N] " confirm
    [[ "${confirm}" =~ ^[Yy]$ ]] || { info "Annulé"; exit 0; }

    kind delete cluster --name "${CLUSTER_NAME}" 2>/dev/null && \
        success "Cluster kind supprimé" || true

    docker stop "${REGISTRY_NAME}" 2>/dev/null && \
        docker rm "${REGISTRY_NAME}" 2>/dev/null && \
        success "Registry supprimé" || true

    docker stop "${GITEA_NAME}" 2>/dev/null && \
        docker rm "${GITEA_NAME}" 2>/dev/null && \
        success "Gitea supprimé" || true

    warning "Volume gitea-data conservé (données Gitea). Pour supprimer : docker volume rm gitea-data"
}

# ── Setup complet ──────────────────────────────────────────────────────────────
cmd_setup() {
    check_prereqs
    setup_registry
    setup_gitea
    setup_kind
    setup_argocd
    setup_act

    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  Pipeline local prêt !                                        ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "║  Étapes suivantes :                                           ║"
    echo "║  1. Créer un compte admin sur http://localhost:${GITEA_PORT}          ║"
    echo "║  2. Créer le repo 'chatbot-api' sur Gitea                     ║"
    echo "║  3. cp .secrets.act.example .secrets.act  (adapter les clés)  ║"
    echo "║  4. git remote add local http://localhost:${GITEA_PORT}/<USER>/...    ║"
    echo "║  5. git push local main                                       ║"
    echo "║  6. ./scripts/setup-local-pipeline.sh ci   (lancer le CI)    ║"
    echo "║  7. kubectl apply -f k8s/argocd/application.yaml              ║"
    echo "║  8. kubectl port-forward svc/argocd-server -n argocd 8081:443 ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Voir docs/LOCAL_PIPELINE.md pour le guide complet."
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case "${1:-help}" in
    setup)       cmd_setup ;;
    ci)          shift; cmd_ci "$@" ;;
    push-image)  cmd_push_image ;;
    sync)        cmd_sync ;;
    status)      cmd_status ;;
    destroy)     cmd_destroy ;;
    *)
        echo "Usage : $0 {setup|ci|push-image|sync|status|destroy}"
        echo ""
        echo "  setup       — Installation complète (registry + Gitea + kind + ArgoCD)"
        echo "  ci          — Lance le CI avec act (GitHub Actions local)"
        echo "  push-image  — Build et push de l'image vers le registry local"
        echo "  sync        — Déclenche la synchronisation ArgoCD"
        echo "  status      — Affiche le statut de tous les composants"
        echo "  destroy     — Supprime tous les composants"
        ;;
esac
