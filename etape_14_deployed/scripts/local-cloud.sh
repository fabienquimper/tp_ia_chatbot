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

# ── Détection plateforme & port-forward ───────────────────────────────────────

# Retourne 0 si on tourne sous WSL2
is_wsl() {
    grep -qi microsoft /proc/version 2>/dev/null
}

# L'API répond-elle déjà sur 127.0.0.1:8080 ?
_api_reachable() {
    curl -sf --max-time 2 "http://127.0.0.1:8080/health" >/dev/null 2>&1
}

PF_PID_FILE="/tmp/chatbot-pf-8080.pid"

# Démarre un port-forward kubectl en arrière-plan si l'API n'est pas joignable.
# Idempotent : no-op si l'API répond déjà.
# Nécessaire sur WSL2 (routage IPv6/ingress cassé) et sur tout cluster multi-nœuds
# où l'ingress-nginx n'est pas sur le nœud avec le port mapping.
ensure_port_forward() {
    if _api_reachable; then
        return 0
    fi

    # Tue un éventuel PF fantôme (process mort mais PID file restant)
    if [ -f "${PF_PID_FILE}" ]; then
        kill "$(cat "${PF_PID_FILE}")" 2>/dev/null || true
        rm -f "${PF_PID_FILE}"
    fi

    if is_wsl; then
        info "WSL2 détecté — l'ingress n'est pas routé, démarrage du port-forward..."
    else
        info "API non joignable via l'ingress — démarrage du port-forward..."
    fi

    kubectl port-forward svc/chatbot-api 8080:80 \
        -n "${NAMESPACE}" --address=0.0.0.0 \
        >>/tmp/chatbot-pf.log 2>&1 &
    echo $! > "${PF_PID_FILE}"

    # Attend que le port-forward soit opérationnel (max 20s)
    local elapsed=0
    printf "  Attente de l'API"
    while ! _api_reachable; do
        elapsed=$((elapsed + 1))
        if [ "${elapsed}" -ge 20 ]; then
            echo ""
            error "Port-forward timeout. Vérifier : kubectl logs deployment/chatbot-api -n ${NAMESPACE}"
        fi
        printf "."
        sleep 1
    done
    echo " OK"
    success "API accessible sur http://127.0.0.1:8080"
}

# Vérifie/restaure l'accès à l'API. Appelable via 'make k8s-check-api'.
cmd_check_api() {
    if _api_reachable; then
        success "API joignable sur http://127.0.0.1:8080"
        curl -s http://127.0.0.1:8080/health | python3 -m json.tool 2>/dev/null || true
    else
        ensure_port_forward
        curl -s http://127.0.0.1:8080/health | python3 -m json.tool 2>/dev/null || true
    fi
}

# ─────────────────────────────────────────────────────────────────────────────

CLUSTER_NAME="chatbot-local"
NAMESPACE="chatbot"
IMAGE="chatbot-api:local"
IMAGE="ghcr.io/fabienquimper/chatbot-api:latest"

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
        hostPort: 9093      # Prometheus → http://localhost:9093 (9090 occupé par process orphelin)
        protocol: TCP
EOF
)

# ── Commandes ─────────────────────────────────────────────────────────────────

cmd_setup() {
    info "Création du cluster kind '${CLUSTER_NAME}'..."
    command -v kind >/dev/null 2>&1 || error "kind non installé. Voir https://kind.sigs.k8s.io/docs/user/quick-start/"
    command -v kubectl >/dev/null 2>&1 || error "kubectl non installé."

    # Vérifie que le port 8080 est libre avant de tenter la création du cluster
    if docker ps --format '{{.Ports}}' 2>/dev/null | grep -q '0.0.0.0:8080->'; then
        local owner
        owner=$(docker ps --format '{{.Names}}\t{{.Ports}}' | grep '0.0.0.0:8080->' | awk '{print $1}')
        echo ""
        echo -e "${RED}[ERROR]${NC} Le port 8080 est déjà alloué par : ${owner}"
        echo ""
        echo "  → Libérez-le avec : make k8s-clean"
        echo "    (supprime le cluster conflictuel + le port-forward)"
        echo ""
        exit 1
    fi

    # Crée le cluster
    echo "${KIND_CONFIG}" | kind create cluster --config=-
    success "Cluster créé"

    # Install Nginx Ingress Controller (adapté pour kind)
    info "Installation de Nginx Ingress Controller..."
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
    kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx --timeout=120s
    success "Ingress Controller prêt"

    # Install cert-manager (TLS local — optionnel, peut échouer si GitHub injoignable)
    info "Installation de cert-manager (optionnel)..."
    if kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.7/cert-manager.yaml 2>/dev/null; then
        kubectl rollout status deployment/cert-manager -n cert-manager --timeout=120s 2>/dev/null || true
        kubectl rollout status deployment/cert-manager-webhook -n cert-manager --timeout=120s 2>/dev/null || true
        success "cert-manager prêt"
    else
        warning "cert-manager non installé (GitHub injoignable ou timeout) — TLS désactivé, l'app fonctionne en HTTP"
    fi

    success "Cluster '${CLUSTER_NAME}' opérationnel !"
    info "API sera accessible sur : http://127.0.0.1:8080  (port-forward auto si WSL2)"
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

    # Injection des variables .env dans le ConfigMap
    # xargs trimme les espaces — le .env a des commentaires qui laissent des espaces en fin de valeur
    local _mode _url _model
    _mode=$(echo "${MODE:-local}"        | xargs)
    _url=$(echo  "${LOCAL_BASE_URL:-}"   | xargs)
    _model=$(echo "${LOCAL_MODEL:-}"     | xargs)
    kubectl patch configmap chatbot-config -n "${NAMESPACE}" --type merge \
        -p "{\"data\":{\"MODE\":\"${_mode}\",\"LOCAL_BASE_URL\":\"${_url}\",\"LOCAL_MODEL\":\"${_model}\"}}"

    # Patch ingress : supprime host et TLS (inutiles en local kind)
    kubectl patch ingress chatbot-ingress -n "${NAMESPACE}" --type=json -p='[
      {"op":"remove","path":"/spec/tls"},
      {"op":"remove","path":"/spec/rules/0/host"},
      {"op":"replace","path":"/metadata/annotations/nginx.ingress.kubernetes.io~1ssl-redirect","value":"false"},
      {"op":"replace","path":"/metadata/annotations/nginx.ingress.kubernetes.io~1force-ssl-redirect","value":"false"}
    ]' 2>/dev/null || true

    # Redémarre les pods pour qu'ils chargent les nouvelles valeurs du ConfigMap
    info "Redémarrage des pods (chargement des variables .env)..."
    kubectl rollout restart deployment/chatbot-api -n "${NAMESPACE}"
    info "Attente du déploiement..."
    kubectl rollout status deployment/chatbot-api -n "${NAMESPACE}" --timeout=3m

    success "Application déployée !"
    echo ""
    kubectl get pods -n "${NAMESPACE}"
    echo ""

    # Assure l'accès à l'API (port-forward automatique si l'ingress n'est pas routé)
    ensure_port_forward

    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║  Cloud local opérationnel !               ║"
    echo "╠════════════════════════════════════════════╣"
    echo "║  API   : http://127.0.0.1:8080/docs        ║"
    echo "║  Health: http://127.0.0.1:8080/health      ║"
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

cmd_index_rag() {
    # Récupère l'image et la pull policy du deployment en cours
    local image pull_policy
    image=$(kubectl get deployment chatbot-api -n "${NAMESPACE}" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)
    pull_policy=$(kubectl get deployment chatbot-api -n "${NAMESPACE}" \
        -o jsonpath='{.spec.template.spec.containers[0].imagePullPolicy}' 2>/dev/null)

    if [ -z "${image}" ]; then
        error "chatbot-api non déployé. Lancer make deploy-k8s-local ou make deploy-k8s-image d'abord."
    fi

    info "Image : ${image} (pullPolicy: ${pull_policy})"
    info "Lancement du Job d'indexation RAG (mémoire dédiée : 1Gi)..."

    # Supprime un job précédent éventuel
    kubectl delete job rag-indexer -n "${NAMESPACE}" --ignore-not-found 2>/dev/null

    # Crée un Job K8S temporaire avec le même PVC mais plus de mémoire
    kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: rag-indexer
  namespace: ${NAMESPACE}
spec:
  ttlSecondsAfterFinished: 120
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: indexer
          image: ${image}
          imagePullPolicy: IfNotPresent   # l'image est déjà sur le nœud kind
          command:
            - python
            - scripts/index_rag.py
            - --docs-dir
            - /app/docs
            - --chroma-dir
            - /app/data/chroma_db
          resources:
            requests:
              memory: "512Mi"
            limits:
              memory: "1Gi"    # l'API est à 512Mi — le modèle ONNX a besoin de plus
          volumeMounts:
            - name: data
              mountPath: /app/data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: chatbot-data-pvc
EOF

    info "Indexation en cours (téléchargement modèle ONNX ~80Mo la première fois)..."
    kubectl wait --for=condition=complete job/rag-indexer \
        -n "${NAMESPACE}" --timeout=5m
    echo ""
    kubectl logs job/rag-indexer -n "${NAMESPACE}"
    kubectl delete job rag-indexer -n "${NAMESPACE}" --ignore-not-found 2>/dev/null

    # Redémarre l'API pour qu'elle recharge la collection ChromaDB (nouveau UUID après re-index)
    info "Redémarrage de l'API pour recharger la collection..."
    kubectl rollout restart deployment/chatbot-api -n "${NAMESPACE}"
    kubectl rollout status deployment/chatbot-api -n "${NAMESPACE}" --timeout=60s

    # Le redémarrage coupe le port-forward s'il était actif — on le relance
    rm -f "${PF_PID_FILE}"
    ensure_port_forward

    success "Indexation terminée !"
    echo ""
    curl -sf http://127.0.0.1:8080/health \
        | python3 -c "import sys,json; h=json.load(sys.stdin); print('  rag_available:', h['rag_available'])" \
        2>/dev/null || true
}

cmd_deploy_local_image() {
    local build_path="${BUILD_PATH:-../etape_13_deployable}"

    # 1. Build l'image locale
    info "Build de l'image locale depuis '${build_path}'..."
    docker build -t chatbot-api:local "${build_path}"
    success "Image chatbot-api:local créée"
    echo ""

    # 2. Charger l'image dans le cluster kind (le cluster ne voit pas le daemon Docker local)
    # Vérifie d'abord si l'image est déjà présente pour éviter un transfert inutile de ~640Mo
    local local_digest kind_digest
    local_digest=$(docker inspect --format='{{index .RepoDigests 0}}' chatbot-api:local 2>/dev/null \
                   || docker inspect --format='{{.Id}}' chatbot-api:local 2>/dev/null)
    kind_digest=$(docker exec "${CLUSTER_NAME}-control-plane" \
                    crictl inspecti chatbot-api:local 2>/dev/null \
                    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status']['id'])" \
                    2>/dev/null || echo "")

    if [ -n "${kind_digest}" ] && echo "${local_digest}" | grep -q "${kind_digest:0:12}"; then
        success "Image chatbot-api:local déjà présente dans le cluster — chargement ignoré"
    else
        info "Chargement de l'image dans le cluster kind '${CLUSTER_NAME}' (~640Mo, patience)..."
        # Utilise docker save | ctr import pour avoir un retour de progression
        docker save chatbot-api:local \
            | docker exec -i "${CLUSTER_NAME}-control-plane" \
                ctr -n=k8s.io images import -
        success "Image disponible dans le cluster"
    fi
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

    # 5. Déploiement via l'overlay kustomize (image locale, imagePullPolicy Never, ingress local)
    info "Déploiement des manifests (overlay image locale)..."
    kubectl apply -k overlays/local-image/

    # Injection des variables .env dans le ConfigMap
    # xargs trimme les espaces — le .env a des commentaires qui laissent des espaces en fin de valeur
    local _mode _url _model
    _mode=$(echo "${MODE:-local}"        | xargs)
    _url=$(echo  "${LOCAL_BASE_URL:-}"   | xargs)
    _model=$(echo "${LOCAL_MODEL:-}"     | xargs)
    kubectl patch configmap chatbot-config -n "${NAMESPACE}" --type merge \
        -p "{\"data\":{\"MODE\":\"${_mode}\",\"LOCAL_BASE_URL\":\"${_url}\",\"LOCAL_MODEL\":\"${_model}\"}}"

    # Redémarre les pods pour qu'ils chargent les nouvelles valeurs du ConfigMap
    info "Redémarrage des pods (chargement des variables .env)..."
    kubectl rollout restart deployment/chatbot-api -n "${NAMESPACE}"

    # 6. Attente
    info "Attente que les pods soient Running..."
    kubectl rollout status deployment/chatbot-api -n "${NAMESPACE}" --timeout=3m
    echo ""

    success "Application déployée depuis l'image locale !"
    echo ""
    kubectl get pods -n "${NAMESPACE}"
    echo ""

    # Assure l'accès à l'API (port-forward automatique si l'ingress n'est pas routé)
    ensure_port_forward

    echo ""
    echo "╔════════════════════════════════════════════════╗"
    echo "║   Cluster K8S (image locale) opérationnel !   ║"
    echo "╠════════════════════════════════════════════════╣"
    echo "║  API       : http://127.0.0.1:8080/docs        ║"
    echo "║  Health    : http://127.0.0.1:8080/health      ║"
    echo "║  Prometheus: http://localhost:9090             ║"
    echo "║  Grafana   : http://localhost:3000             ║"
    echo "╚════════════════════════════════════════════════╝"
}

cmd_destroy() {
    # Tue le port-forward associé avant de supprimer le cluster
    _kill_port_forward

    warning "Suppression du cluster '${CLUSTER_NAME}'..."
    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        kind delete cluster --name "${CLUSTER_NAME}"
        success "Cluster '${CLUSTER_NAME}' supprimé"
    else
        warning "Cluster '${CLUSTER_NAME}' introuvable — rien à supprimer"
    fi
}

# Arrête proprement le port-forward kubectl sur 8080
_kill_port_forward() {
    if [ -f "${PF_PID_FILE}" ]; then
        kill "$(cat "${PF_PID_FILE}")" 2>/dev/null || true
        rm -f "${PF_PID_FILE}"
    fi
    # Tue aussi tout kubectl port-forward résiduel sur ce port (PID file manquant)
    pkill -f "kubectl port-forward.*8080" 2>/dev/null || true
}

# Libère le port 8080 : détruit tout cluster kind qui l'occupe + le port-forward.
# À utiliser avant make k8s-setup si le port est déjà alloué.
cmd_clean() {
    info "Nettoyage de l'environnement K8S local (libération du port 8080)..."

    # 1. Tue le port-forward kubectl
    _kill_port_forward
    info "Port-forward arrêté"

    # 2. Détruit tous les clusters kind qui ont le port 8080 mappé
    local found=0
    for cluster in $(kind get clusters 2>/dev/null); do
        if docker ps --format '{{.Names}}\t{{.Ports}}' 2>/dev/null \
               | grep "${cluster}" | grep -q '0.0.0.0:8080->'; then
            warning "Cluster '${cluster}' occupe le port 8080 — suppression..."
            kind delete cluster --name "${cluster}"
            success "Cluster '${cluster}' supprimé"
            found=1
        fi
    done

    # 3. Détruit aussi le cluster cible s'il existe encore (cluster sans port mapping actif)
    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        warning "Suppression du cluster cible '${CLUSTER_NAME}'..."
        kind delete cluster --name "${CLUSTER_NAME}"
        success "Cluster '${CLUSTER_NAME}' supprimé"
        found=1
    fi

    [ "${found}" -eq 0 ] && info "Aucun cluster à supprimer — port 8080 déjà libre"

    success "Environnement propre — lancez : make k8s-setup"
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case "${1:-help}" in
    setup)              cmd_setup ;;
    deploy)             cmd_deploy ;;
    deploy-local-image) cmd_deploy_local_image ;;
    index-rag)          cmd_index_rag ;;
    check-api)          cmd_check_api ;;
    clean)              cmd_clean ;;
    status)             cmd_status ;;
    destroy)            cmd_destroy ;;
    *)
        echo "Usage : $0 {setup|deploy|deploy-local-image|index-rag|check-api|clean|status|destroy}"
        echo ""
        echo "  setup               — Crée le cluster kind local"
        echo "  deploy              — Déploie depuis GHCR (nécessite REGISTRY_TOKEN)"
        echo "  deploy-local-image  — Build + charge l'image locale, déploie sans GHCR"
        echo "  index-rag           — Indexe les documents RAG dans un Job K8S dédié"
        echo "  check-api           — Vérifie/restaure l'accès à l'API (port-forward si besoin)"
        echo "  clean               — Libère le port 8080 (clusters + port-forward) avant k8s-setup"
        echo "  status              — Affiche le statut"
        echo "  destroy             — Supprime le cluster '${CLUSTER_NAME}'"
        ;;
esac
