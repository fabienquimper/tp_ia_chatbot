# Étape 14 — Deployed

Exemples de déploiement en production : GitHub Actions CI/CD, Docker Compose sur VPS,
Kubernetes (local avec `kind` et cloud GCP/AWS).

> **Prérequis** : avoir complété l'étape 13. L'image Docker produite par l'étape 13
> est la base de tout ce qui suit ici.

---

## Structure

```
etape_14_deployed/
├── .github/workflows/
│   ├── ci.yml          # Tests + lint + sécurité sur chaque push/PR
│   ├── cd.yml          # Build → Push GHCR → Deploy sur merge/tag
│   └── security.yml    # Audit sécurité hebdomadaire (Trivy + Safety)
│
├── k8s/                # Manifests Kubernetes
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml     # ⚠️ Ne jamais committer avec de vraies valeurs
│   ├── pvc.yaml        # Volumes persistants (data + chroma + grafana)
│   ├── chatbot-deployment.yaml  # Deployment + init container RAG
│   ├── chatbot-service.yaml
│   ├── chatbot-hpa.yaml         # Autoscale 2 → 10 replicas
│   ├── ingress.yaml             # Nginx Ingress + TLS cert-manager
│   ├── kustomization.yaml
│   ├── monitoring/
│   │   ├── prometheus-deployment.yaml        # Prometheus + ConfigMap + RBAC
│   │   ├── grafana-deployment.yaml           # Grafana + montage provisioning
│   │   └── grafana-provisioning-configmap.yaml  # Datasource uid:prometheus + dashboard provider
│   └── argocd/
│       └── application.yaml      # Application ArgoCD (GitOps local)
│
├── docker/
│   ├── docker-compose.prod.yml  # Compose tirant l'image depuis GHCR
│   └── nginx/nginx.conf
│
├── scripts/
│   ├── deploy-docker.sh          # Déploiement VPS via SSH
│   ├── deploy-k8s.sh             # Déploiement cluster K8S
│   ├── local-cloud.sh            # Simulation cloud local avec kind
│   └── setup-local-pipeline.sh  # Pipeline CI/CD complet (registry+Gitea+kind+ArgoCD)
│
└── docs/
    ├── DEPLOY_GCP.md        # Google Cloud Run + GKE
    ├── DEPLOY_AWS.md        # AWS ECS Fargate + EKS
    ├── DEPLOY_LOCAL_K8S.md  # K8S local avec kind (pas de compte cloud requis)
    └── LOCAL_PIPELINE.md    # Pipeline CI/CD complet local (act + Gitea + ArgoCD)
```

---

## Choisir son déploiement

```
Besoin                          Solution recommandée
─────────────────────────────────────────────────────
Tester K8S sans compte cloud  → Local avec kind
Pipeline CI/CD visuel local   → act + Gitea + ArgoCD + kind
1 serveur, budget limité       → Docker Compose VPS
Serverless, scale to zero      → Google Cloud Run
Déjà sur AWS                   → ECS Fargate
Forte charge, équipe DevOps    → GKE ou EKS
```

---

## Option 0 — Pipeline CI/CD local complet (act + Gitea + ArgoCD + kind)

Pour simuler un pipeline de production **entier** sur votre machine : CI/CD, registry, Git server, GitOps.

```
git push → Gitea → act (CI) → registry:5001 → ArgoCD → kind (K8S)
```

```bash
# Installation complète en une commande
./scripts/setup-local-pipeline.sh setup

# Lancer le CI localement (lint + tests + docker build)
./scripts/setup-local-pipeline.sh ci

# Build et push l'image vers le registry local
./scripts/setup-local-pipeline.sh push-image

# Voir l'état de tout le pipeline
./scripts/setup-local-pipeline.sh status
```

Voir `docs/LOCAL_PIPELINE.md` pour le guide complet avec ArgoCD, les webhooks, et le workflow de développement.

---

## Option 1 — Docker Compose sur VPS (le plus simple)

Idéal pour un premier déploiement réel.

```bash
# Depuis votre machine locale
./scripts/deploy-docker.sh --host user@votre-serveur.com
```

Le script :
1. Se connecte en SSH
2. Clone le repo
3. Configure le `.env`
4. Lance `docker compose -f docker/docker-compose.prod.yml up -d`

L'image est tirée depuis GitHub Container Registry (GHCR) — pas de build sur le serveur.

---

## Option 2 — Kubernetes local avec kind

Pour tester les manifests K8S **sans compte cloud**.

```bash
# Prérequis : kind + kubectl installés
# Installation : https://kind.sigs.k8s.io/docs/user/quick-start/

# Créer le cluster (1 control-plane + 2 workers + nginx ingress + cert-manager)
./scripts/local-cloud.sh setup

# Déployer le chatbot
OPENAI_API_KEY="sk-..." ./scripts/local-cloud.sh deploy

# Voir l'état
./scripts/local-cloud.sh status

# Scaler manuellement
kubectl scale deployment chatbot-api --replicas=3 -n chatbot

# Supprimer le cluster
./scripts/local-cloud.sh destroy
```

Voir `docs/DEPLOY_LOCAL_K8S.md` pour le guide complet (rollback, HPA, logs).

---

## Option 3 — Google Cloud

### Cloud Run (serverless, recommandé pour démarrer)

```bash
# Authentification
gcloud auth login
gcloud config set project MON_PROJET

# Build et push vers Artifact Registry
gcloud builds submit --tag europe-west1-docker.pkg.dev/MON_PROJET/chatbot/api

# Déploiement
gcloud run deploy chatbot-api \
  --image europe-west1-docker.pkg.dev/MON_PROJET/chatbot/api \
  --region europe-west1 \
  --set-secrets OPENAI_API_KEY=openai-key:latest \
  --min-instances 0 --max-instances 10
```

Voir `docs/DEPLOY_GCP.md` pour le guide complet incluant GKE.

---

## Option 4 — AWS

### ECS Fargate (serverless)

```bash
# Push vers ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker push $ECR_URI/chatbot-api:latest

# Créer la task definition et le service ECS
aws ecs create-service --cli-input-json file://ecs-service.json
```

Voir `docs/DEPLOY_AWS.md` pour ECS Fargate et EKS.

---

## CI/CD avec GitHub Actions

### Configurer les secrets GitHub

Dans `Settings → Secrets and variables → Actions` de votre repo :

| Secret | Description |
|---|---|
| `STAGING_HOST` | IP du serveur staging |
| `STAGING_USER` | Utilisateur SSH |
| `STAGING_SSH_KEY` | Clé privée SSH |
| `PROD_HOST` | IP du serveur production |
| `PROD_USER` | Utilisateur SSH prod |
| `PROD_SSH_KEY` | Clé privée SSH prod |

`GITHUB_TOKEN` est automatiquement disponible (push GHCR).

### Pipeline automatique

```
Push / PR  →  ci.yml
               ├── ruff (lint)
               ├── pytest (70% coverage requis)
               ├── bandit + safety (sécurité)
               └── docker build (validation)

Merge main →  cd.yml
               ├── Tests obligatoires
               ├── Build + Push → ghcr.io/org/chatbot-api:sha
               ├── Tag :latest
               └── Deploy → Staging (auto)

Tag v*.*.* →  cd.yml (suite)
               └── Deploy → Production

Hebdomadaire → security.yml
               ├── Safety (dépendances)
               └── Trivy (image Docker) → GitHub Security tab
```

### Déclencher manuellement

```bash
# Déployer en staging
gh workflow run cd.yml --field environment=staging

# Déployer en production via tag
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

---

## Kubernetes — concepts clés

### HPA (autoscaling automatique)

Le `chatbot-hpa.yaml` configure l'autoscale entre 2 et 10 replicas :
- Scale up si CPU > 70% ou mémoire > 80%
- Scale down après 5 min de charge réduite

```bash
kubectl get hpa -n chatbot            # voir l'état
kubectl describe hpa chatbot-api -n chatbot
```

### Rollback

```bash
# Voir l'historique
kubectl rollout history deployment/chatbot-api -n chatbot

# Revenir en arrière
kubectl rollout undo deployment/chatbot-api -n chatbot

# Revenir à une version précise
kubectl rollout undo deployment/chatbot-api --to-revision=2 -n chatbot
```

### Secrets (ne jamais committer les vraies valeurs)

```bash
# Créer le secret depuis les variables d'environnement
kubectl create secret generic chatbot-secrets \
  --from-literal=OPENAI_API_KEY="sk-..." \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  -n chatbot
```

Le fichier `k8s/secret.yaml` contient des **placeholders** — remplacer avant d'appliquer.

---

## Rollback Docker Compose

```bash
# Revenir à une image précédente
IMAGE_TAG=v1.2.2 docker compose -f docker/docker-compose.prod.yml up -d --no-build
```

---

## Monitoring (Prometheus + Grafana)

### Docker Compose

Le fichier `docker/docker-compose.prod.yml` référence directement les fichiers de configuration
de l'étape 13 — **aucune configuration supplémentaire requise** :

```
../etape_13_deployable/prometheus.yml              → config Prometheus
../etape_13_deployable/prometheus-alerts.yml       → règles d'alerte
../etape_13_deployable/grafana/provisioning/       → datasource + dashboard automatiques
```

Grafana est accessible à `https://votre-domaine/grafana` — le dashboard se charge automatiquement.

---

### Kubernetes

#### 1. Déployer le stack monitoring

```bash
kubectl apply -f k8s/monitoring/grafana-provisioning-configmap.yaml
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml
kubectl apply -f k8s/monitoring/grafana-deployment.yaml
```

#### 2. Accéder à Grafana

```bash
kubectl port-forward svc/grafana 3000:3000 -n chatbot
# → http://localhost:3000
# Login : admin / (valeur du secret grafana-password)
```

#### 3. Importer le dashboard

La datasource Prometheus est configurée automatiquement (uid `prometheus`).
Le dashboard doit être importé manuellement **une seule fois** :

1. Grafana → **Dashboards → Import**
2. Cliquer **Upload JSON file**
3. Sélectionner :
   ```
   etape_13_deployable/grafana/provisioning/dashboards/chatbot.json
   ```
4. Cliquer **Import**

> **Pourquoi manuel en K8s ?** Le JSON fait 550+ lignes — trop verbeux pour un ConfigMap inline.
> Alternative : créer un ConfigMap dédié et le monter dans `/var/lib/grafana/dashboards/`
> (le dashboard provider est déjà configuré pour ce chemin dans `grafana-provisioning-configmap.yaml`).

#### 4. Vérifier que les métriques arrivent

```bash
# Prometheus scrape le chatbot ?
kubectl port-forward svc/prometheus 9090:9090 -n chatbot
# → http://localhost:9090/targets  (chatbot-api doit être UP)
```
