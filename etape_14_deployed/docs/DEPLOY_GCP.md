# Déploiement sur Google Cloud Platform

Deux options principales : **Cloud Run** (serverless, simple) ou **GKE** (Kubernetes, complet).

---

## Option 1 — Cloud Run (recommandé pour démarrer)

Cloud Run gère automatiquement le scaling (y compris à zéro), sans gérer de serveurs.

### Prérequis

```bash
# Installer Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
```

### Étapes

#### 1. Créer un registry Artifact Registry

```bash
gcloud artifacts repositories create chatbot \
  --repository-format=docker \
  --location=europe-west1 \
  --description="Chatbot IA Docker repository"

# Authentification Docker
gcloud auth configure-docker europe-west1-docker.pkg.dev
```

#### 2. Build et push de l'image

```bash
IMAGE="europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/chatbot/chatbot-api"

docker build --target production \
  -t "${IMAGE}:latest" \
  etape_13_deployable/

docker push "${IMAGE}:latest"
```

#### 3. Stocker les secrets dans Secret Manager

```bash
# Créer les secrets
echo -n "sk-your-openai-key" | \
  gcloud secrets create chatbot-openai-key --data-file=-

echo -n "$(openssl rand -hex 32)" | \
  gcloud secrets create chatbot-secret-key --data-file=-

# Donner accès au service account Cloud Run
gcloud secrets add-iam-policy-binding chatbot-openai-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### 4. Déploiement Cloud Run

```bash
gcloud run deploy chatbot-api \
  --image "${IMAGE}:latest" \
  --region europe-west1 \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 10 \
  --concurrency 80 \
  --timeout 120 \
  --set-env-vars "MODEL=gpt-4o-mini,MODE=cloud" \
  --set-secrets "OPENAI_API_KEY=chatbot-openai-key:latest,SECRET_KEY=chatbot-secret-key:latest" \
  --allow-unauthenticated \
  --port 8000

# Récupérer l'URL
gcloud run services describe chatbot-api \
  --region europe-west1 \
  --format 'value(status.url)'
```

#### 5. Volume persistant (SQLite + ChromaDB)

> Cloud Run est stateless. Pour la persistance, utiliser **Cloud Filestore** (NFS) ou **Cloud SQL** en remplacement de SQLite.

```bash
# Créer un volume NFS (Cloud Filestore)
gcloud filestore instances create chatbot-data \
  --zone=europe-west1-b \
  --tier=BASIC_HDD \
  --file-share=name=chatbot,capacity=1TB \
  --network=name=default

# Monter dans Cloud Run (annotation réseau VPC requis)
gcloud run services update chatbot-api \
  --add-volume name=chatbot-data,type=nfs,location=FILESTORE_IP,path=/chatbot \
  --add-volume-mount volume=chatbot-data,mount-path=/app/data \
  --region europe-west1
```

#### 6. Custom Domain + HTTPS

```bash
gcloud run domain-mappings create \
  --service chatbot-api \
  --domain chatbot.your-domain.com \
  --region europe-west1
# Ajouter l'entrée DNS CNAME indiquée par GCP
```

---

## Option 2 — GKE (Google Kubernetes Engine)

Pour un déploiement complet avec les manifests K8S de l'étape 14.

### Créer le cluster GKE

```bash
# Cluster Autopilot (recommandé — gestion automatique des nodes)
gcloud container clusters create-auto chatbot-cluster \
  --region europe-west1

# Configurer kubectl
gcloud container clusters get-credentials chatbot-cluster \
  --region europe-west1
```

### Déployer avec les manifests K8S

```bash
# Adapter les images dans kustomization.yaml
IMAGE="europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/chatbot/chatbot-api"

cd etape_14_deployed/k8s
# Remplacer YOUR_ORG par l'image GCP
sed -i "s|ghcr.io/YOUR_ORG/chatbot-api|${IMAGE}|g" \
  chatbot-deployment.yaml kustomization.yaml

# Créer les secrets
kubectl create secret generic chatbot-secrets \
  --from-literal=openai-api-key="$(gcloud secrets versions access latest --secret=chatbot-openai-key)" \
  --from-literal=secret-key="$(gcloud secrets versions access latest --secret=chatbot-secret-key)" \
  --from-literal=grafana-password="strong-password" \
  -n chatbot

# Déployer
kubectl apply -k .
```

### Ingress GKE avec TLS managé

```bash
# Utiliser le GKE Ingress natif (pas nginx)
# Remplacer l'annotation ingressClassName dans ingress.yaml :
# spec:
#   ingressClassName: ""     (GKE gère le LB automatiquement)

# Certificate managé par GCP
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: ManagedCertificate
metadata:
  name: chatbot-cert
  namespace: chatbot
spec:
  domains:
    - chatbot.your-domain.com
EOF
```

---

## Monitoring sur GCP

- **Cloud Monitoring** : intégration native avec les métriques Prometheus via l'agent
- **Cloud Logging** : les logs des conteneurs sont automatiquement collectés
- **Cloud Trace** : traçage distribué (ajouter opentelemetry si besoin)

```bash
# Activer le monitoring Prometheus sur GKE
gcloud container clusters update chatbot-cluster \
  --enable-managed-prometheus \
  --region europe-west1
```

---

## Estimation des coûts (Europe West 1)

| Service | Configuration | Coût estimé/mois |
|---|---|---|
| Cloud Run | 1 instance, 512Mi, ~1000 req/j | ~5-15€ |
| GKE Autopilot | 2 pods 512Mi | ~50-80€ |
| Artifact Registry | ~1GB images | ~0.10€ |
| Filestore (NFS) | 1TB HDD | ~200€ |
| Secret Manager | < 10 secrets | ~0€ |

> Les prix varient. Utiliser le [calculateur GCP](https://cloud.google.com/products/calculator).
