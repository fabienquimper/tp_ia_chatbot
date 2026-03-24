# Déploiement K8S local avec kind

Simule un cluster Kubernetes complet sur votre machine en quelques commandes.
Idéal pour tester les manifests avant de déployer en cloud.

---

## Prérequis

```bash
# macOS
brew install kind kubectl

# Windows (PowerShell en admin)
choco install kind kubernetes-cli

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
```

Vérifier :
```bash
kind version      # kind v0.22.0+
kubectl version   # Client Version: v1.28+
docker version    # Docker Engine installé
```

---

## Démarrage rapide (3 commandes)

```bash
# 1. Créer le cluster (1 control-plane + 2 workers)
./scripts/local-cloud.sh setup

# 2. Déployer l'application
OPENAI_API_KEY="sk-votre-cle" ./scripts/local-cloud.sh deploy

# 3. Tester
curl http://localhost:8080/health
```

---

## Détail des étapes manuelles

### 1. Créer le cluster kind

```bash
cat > kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
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
      - containerPort: 443
        hostPort: 8443
  - role: worker
  - role: worker
EOF

kind create cluster --config kind-config.yaml --name chatbot-local
```

### 2. Nginx Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

### 3. Build et chargement de l'image

```bash
# Build (depuis la racine du projet)
docker build --target production \
  -t chatbot-api:local \
  etape_13_deployable/

# Charger dans kind (évite le pull depuis un registry)
kind load docker-image chatbot-api:local --name chatbot-local
```

### 4. Créer les secrets

```bash
kubectl create namespace chatbot

kubectl create secret generic chatbot-secrets \
  --from-literal=openai-api-key="sk-votre-cle" \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=grafana-password="admin123" \
  -n chatbot
```

### 5. Adapter les manifests pour l'image locale

```bash
cd etape_14_deployed/k8s

# Remplacer l'image distante par l'image locale
sed -i 's|ghcr.io/YOUR_ORG/chatbot-api:latest|chatbot-api:local|g' \
  chatbot-deployment.yaml

# Mettre imagePullPolicy à Never (image locale)
kubectl patch deployment chatbot-api -n chatbot \
  --patch '{"spec":{"template":{"spec":{"containers":[{"name":"chatbot","imagePullPolicy":"Never"}]}}}}'
```

### 6. Déployer

```bash
kubectl apply -k etape_14_deployed/k8s/

# Attendre le déploiement
kubectl rollout status deployment/chatbot-api -n chatbot --timeout=3m
```

### 7. Adapter l'Ingress pour localhost

```bash
# Modifier ingress.yaml pour accepter localhost
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: chatbot-ingress
  namespace: chatbot
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: localhost
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: chatbot-api
                port:
                  number: 80
EOF
```

---

## Commandes utiles

```bash
# Statut
kubectl get all -n chatbot

# Logs
kubectl logs -f deployment/chatbot-api -n chatbot

# Shell dans un pod
kubectl exec -it \
  $(kubectl get pods -n chatbot -l app=chatbot-api -o jsonpath='{.items[0].metadata.name}') \
  -n chatbot -- /bin/bash

# Port-forward direct (sans Ingress)
kubectl port-forward svc/chatbot-api 8000:80 -n chatbot

# Tester le health check
curl http://localhost:8080/health

# Connexion JWT
TOKEN=$(curl -s -X POST http://localhost:8080/auth/token \
  -d "username=alice&password=password123" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour !"}' \
  http://localhost:8080/chat
```

---

## Scaling manuel (simulation HPA)

```bash
# Scale up à 5 replicas
kubectl scale deployment chatbot-api --replicas=5 -n chatbot

# Vérifier la répartition
kubectl get pods -n chatbot -o wide

# Scale down
kubectl scale deployment chatbot-api --replicas=2 -n chatbot
```

---

## Simulation d'un rolling update

```bash
# Build d'une nouvelle version
docker build --target production \
  -t chatbot-api:v2 \
  etape_13_deployable/

kind load docker-image chatbot-api:v2 --name chatbot-local

# Mise à jour (zero-downtime)
kubectl set image deployment/chatbot-api \
  chatbot=chatbot-api:v2 \
  -n chatbot

# Suivre le rollout
kubectl rollout status deployment/chatbot-api -n chatbot

# Rollback si problème
kubectl rollout undo deployment/chatbot-api -n chatbot
```

---

## Nettoyage

```bash
# Supprimer le namespace (garde le cluster)
kubectl delete namespace chatbot

# Supprimer le cluster entier
kind delete cluster --name chatbot-local
```

---

## Comparaison des outils K8S locaux

| Outil | Avantages | Inconvénients |
|---|---|---|
| **kind** | Léger, multi-nodes, CI-friendly | Moins de plugins que minikube |
| **minikube** | Riche en addons, tunnel intégré | Plus lourd, un seul node |
| **k3d** | Très rapide, basé sur k3s | k3s ≠ k8s (quelques différences) |
| **Docker Desktop** | Intégré sur Mac/Windows | Un seul node, lent |

> Pour ce projet : **kind** recommandé pour sa légèreté et sa compatibilité CI.
