# Pipeline CI/CD local complet

Simule un pipeline de production complet **sans compte cloud** :

```
Code local
    │
    ▼ git push
┌─────────┐       ┌──────────────────────┐
│  Gitea  │──────▶│  act (GitHub Actions) │  CI : lint + tests + docker build
│  :3001  │       │  en local             │       push image → registry local
└─────────┘       └──────────────────────┘
                            │ image poussée
                            ▼
                  ┌──────────────────────┐
                  │  Registry Docker     │  localhost:5001
                  │  local              │  images disponibles pour kind
                  └──────────────────────┘
                            │
                            ▼ ArgoCD surveille le repo
                  ┌──────────────────────┐
                  │  ArgoCD              │  GitOps : sync automatique
                  │  (dans kind)         │  UI visuelle des déploiements
                  └──────────────────────┘
                            │ applique les manifests
                            ▼
                  ┌──────────────────────┐
                  │  kind (K8S local)    │  API :8080, Grafana :3000
                  │  chatbot-api pods    │
                  └──────────────────────┘
```

---

## Prérequis — Installation

### Docker
Déjà nécessaire pour l'étape 13. Vérifier : `docker version`

### kind
```bash
# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# macOS
brew install kind
```

### kubectl
```bash
# Linux
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# macOS
brew install kubectl
```

### act (GitHub Actions local)
```bash
# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# macOS
brew install act
```

### argocd CLI (optionnel — l'UI web suffit)
```bash
# Linux
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd-linux-amd64 && sudo mv argocd-linux-amd64 /usr/local/bin/argocd

# macOS
brew install argocd
```

---

## Démarrage rapide

### 1. Installation complète
```bash
./scripts/setup-local-pipeline.sh setup
```

Ce script installe et configure automatiquement :
- Registry Docker local (port 5001)
- Gitea, serveur Git local (port 3001)
- Cluster kind (1 control-plane + 2 workers) connecté au registry
- ArgoCD dans le cluster kind
- Fichier `.actrc` à la racine du repo

### 2. Configurer Gitea (première fois)

1. Ouvrir http://localhost:3001
2. Cliquer **"Register"** → créer un compte admin
3. Créer un nouveau repository : **"chatbot-api"** (public)
4. Configurer le remote local :
```bash
cd /chemin/vers/le/repo
git remote add local http://localhost:3001/<VOTRE_USER>/chatbot-api.git
git push local main
```

### 3. Configurer les secrets act
```bash
cp .secrets.act.example .secrets.act
# Éditer .secrets.act et adapter OPENAI_API_KEY si nécessaire
```

### 4. Lancer le CI
```bash
# Depuis la racine du repo
./etape_14_deployed/scripts/setup-local-pipeline.sh ci

# Ou directement avec act (pour un job spécifique)
act push --job lint
act push --job tests
act push --job docker-build
```

### 5. Push de l'image vers le registry local
```bash
./scripts/setup-local-pipeline.sh push-image

# Ou manuellement
docker build --target production -t localhost:5001/chatbot-api:latest etape_13_deployable/
docker push localhost:5001/chatbot-api:latest
```

### 6. Configurer ArgoCD

**a. Adapter le fichier Application :**
```bash
# Remplacer GITEA_USER dans k8s/argocd/application.yaml
sed -i 's/GITEA_USER/votre-login-gitea/g' etape_14_deployed/k8s/argocd/application.yaml
```

**b. Configurer les credentials Gitea :**
```bash
kubectl create secret generic gitea-creds \
  --from-literal=username=<VOTRE_USER> \
  --from-literal=password=<VOTRE_MOT_DE_PASSE> \
  -n argocd
kubectl label secret gitea-creds \
  argocd.argoproj.io/secret-type=repository \
  -n argocd
```

**c. Appliquer l'Application ArgoCD :**
```bash
kubectl apply -f etape_14_deployed/k8s/argocd/application.yaml
```

**d. Accéder à l'UI ArgoCD :**
```bash
# Dans un terminal séparé
kubectl port-forward svc/argocd-server -n argocd 8081:443

# Récupérer le mot de passe admin
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

Ouvrir https://localhost:8081 (accepter le certificat auto-signé)
Login : `admin` / mot de passe récupéré ci-dessus

---

## Workflow complet

### Cycle de développement normal

```bash
# 1. Modifier le code
vim etape_13_deployable/app/main.py

# 2. Lancer le CI local (lint + tests)
./etape_14_deployed/scripts/setup-local-pipeline.sh ci

# 3. Build et push l'image
./etape_14_deployed/scripts/setup-local-pipeline.sh push-image

# 4. Pousser le code sur Gitea
git add .
git commit -m "feat: ma nouvelle fonctionnalité"
git push local main

# 5. ArgoCD détecte le changement et déploie automatiquement
# Voir dans l'UI : https://localhost:8081
# Ou surveiller :
kubectl get pods -n chatbot -w
```

### Forcer une synchronisation ArgoCD
```bash
./etape_14_deployed/scripts/setup-local-pipeline.sh sync

# Ou via kubectl
kubectl -n argocd patch application chatbot-api \
  --type merge \
  -p '{"operation":{"sync":{"revision":"HEAD"}}}'
```

---

## Détail des composants

### Registry Docker local (port 5001)

Remplace GHCR (GitHub Container Registry) en local.
Toutes les images sont poussées ici et les nœuds kind les récupèrent.

```bash
# Lister les images disponibles
curl http://localhost:5001/v2/_catalog

# Voir les tags d'une image
curl http://localhost:5001/v2/chatbot-api/tags/list

# Inspecter une image
docker pull localhost:5001/chatbot-api:latest
docker inspect localhost:5001/chatbot-api:latest
```

### Gitea (port 3001)

Serveur Git open-source léger. Joue le rôle de GitHub en local.
ArgoCD surveille ses repos pour déclencher les déploiements.

```bash
# API Gitea
curl http://localhost:3001/api/v1/repos/search | jq '.data[].full_name'

# Webhooks (pour déclencher act automatiquement au push)
# Configurer dans Gitea : Settings → Webhooks → Add webhook
# URL : http://host.docker.internal:PORT (si act expose un endpoint)
```

### kind (port 8080)

Kubernetes in Docker : cluster K8S complet dans des containers Docker.

```bash
# Voir les nœuds
kubectl get nodes

# Changer de cluster (si plusieurs)
kubectl config use-context kind-chatbot-pipeline

# Dashboard K8S (optionnel)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
kubectl proxy &
# → http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

### ArgoCD

Interface visuelle pour voir l'état de synchronisation entre le repo Git et le cluster.

```bash
# Login CLI
argocd login localhost:8081 --username admin --password <PASSWORD> --insecure

# Voir toutes les applications
argocd app list

# Voir le détail
argocd app get chatbot-api

# Synchronisation manuelle
argocd app sync chatbot-api

# Historique des déploiements
argocd app history chatbot-api

# Rollback
argocd app rollback chatbot-api <ID>
```

### act (GitHub Actions local)

Exécute les workflows GitHub Actions sur votre machine sans pousser sur GitHub.

```bash
# Lister les workflows disponibles
act --list

# Lancer le workflow CI complet
act push --workflows etape_14_deployed/.github/workflows/ci.yml

# Lancer un job spécifique
act push --job lint
act push --job tests

# Lancer avec des secrets inline
act push --secret OPENAI_API_KEY=sk-fake

# Mode dry-run (voir ce qui serait exécuté)
act push --dryrun

# Lancer le workflow CD (build + push vers registry local)
act push \
  --workflows etape_14_deployed/.github/workflows/cd.yml \
  --secret REGISTRY=localhost:5001 \
  --env GITHUB_REF=refs/heads/main
```

---

## Adapter les workflows pour le registry local

Le workflow `cd.yml` pousse vers GHCR par défaut. Pour utiliser le registry local avec act, créer un override :

```bash
# .github/workflows/cd.local.yml (ou passer --env en CLI)
# Modifier la variable REGISTRY dans la section env du workflow
```

Ou plus simplement, utiliser le script `push-image` qui bypass les workflows :
```bash
./scripts/setup-local-pipeline.sh push-image
```

---

## Statut et monitoring

```bash
# Statut global du pipeline
./scripts/setup-local-pipeline.sh status

# Pods en temps réel
kubectl get pods -n chatbot -w

# Logs de l'application
kubectl logs -f deployment/chatbot-api -n chatbot

# Logs ArgoCD
kubectl logs -f deployment/argocd-server -n argocd

# Tester l'API
curl http://localhost:8080/health

TOKEN=$(curl -s -X POST http://localhost:8080/auth/token \
  -d "username=alice&password=password123" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour !"}' \
  http://localhost:8080/chat
```

---

## Monitoring (Prometheus + Grafana)

Déployer le stack monitoring dans le cluster local :

```bash
kubectl apply -f etape_14_deployed/k8s/monitoring/grafana-provisioning-configmap.yaml
kubectl apply -f etape_14_deployed/k8s/monitoring/prometheus-deployment.yaml
kubectl apply -f etape_14_deployed/k8s/monitoring/grafana-deployment.yaml

# Accéder à Grafana
kubectl port-forward svc/grafana 3000:3000 -n chatbot &
# → http://localhost:3000  (admin / admin123)

# Importer le dashboard
# Dashboards → Import → Upload JSON file
# → etape_13_deployable/grafana/provisioning/dashboards/chatbot.json
```

---

## Nettoyage

```bash
# Supprimer tout
./scripts/setup-local-pipeline.sh destroy

# Supprimer uniquement le cluster (garde registry + Gitea)
kind delete cluster --name chatbot-pipeline

# Supprimer les données Gitea (irréversible)
docker volume rm gitea-data
```

---

## Comparaison : local vs production

| Composant       | Local (ce guide)              | Production                     |
|-----------------|-------------------------------|--------------------------------|
| Git             | Gitea (localhost:3001)        | GitHub                         |
| CI runner       | `act` (local)                 | GitHub Actions (runners cloud) |
| Registry images | localhost:5001                | GHCR (ghcr.io)                 |
| Kubernetes      | kind (Docker local)           | GKE / EKS / AKS               |
| GitOps          | ArgoCD (dans kind)            | ArgoCD (dans le cluster cloud) |
| TLS             | Pas de TLS                    | cert-manager + Let's Encrypt   |
| Secrets         | `.secrets.act` + K8s secrets  | GitHub Secrets + Vault/SOPS    |

> L'architecture est **identique** — seules les URLs et les credentials changent.
> Un manifest K8S validé en local fonctionnera sur GKE sans modification.
