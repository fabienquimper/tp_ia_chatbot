# Étape 14 — Deployed

> **Prérequis : avoir complété l'étape 13.**
> L'image Docker buildée et poussée sur GHCR à l'étape 13 est la base de tout ce qui suit.

Cette étape propose **trois parcours** selon ce que tu veux apprendre :

```
╔══════════════════════════════════════════════════════════════════╗
║  PARCOURS 0 — "Image locale, tout à la main"    ⏱ ~20 min  ⭐  ║
║  Chaque commande kubectl tapée une par une, sans GHCR            ║
║  Prérequis : Docker, kind, kubectl                               ║
╠══════════════════════════════════════════════════════════════════╣
║  PARCOURS 1 — "Je découvre Kubernetes"          ⏱ ~30 min      ║
║  Déployer l'image GHCR dans un vrai cluster K8S local           ║
║  Prérequis : Docker, kind, kubectl + compte GHCR                 ║
╠══════════════════════════════════════════════════════════════════╣
║  PARCOURS 2 — "Pipeline de release complet"     ⏱ ~2h          ║
║  git tag release0001 → CI → build → push → déploiement auto    ║
║  Prérequis : Docker, kind, kubectl, act + Gitea + ArgoCD        ║
╚══════════════════════════════════════════════════════════════════╝
```

Les trois parcours utilisent les mêmes manifests Kubernetes.
La différence est dans **l'origine de l'image** et **comment le déploiement est déclenché**.

---

## Mise en place commune

### 1. Copier le .env de l'étape 13

```bash
cp ../etape_13_deployable/.env .env
```

> **Parcours 0 uniquement** : le `.env` suffit — pas besoin de GHCR.
> Aller directement à [Parcours 0](#parcours-0--image-locale-tout-à-la-main-).

### 2. Vérifier que l'image est disponible sur GHCR (Parcours 1 et 2 seulement)

```bash
make registry-ls
# → tags=['latest', 'b5b88ec']   id=...   updated=2026-04-11
```

Si aucune image n'apparaît → retourner à l'étape 13 et faire `make build-push`.

---

## Parcours 0 — Image locale, tout à la main ⭐

### Pourquoi commencer ici ?

Le Parcours 1 utilise `make deploy-k8s-local` qui fait tout d'un coup.
C'est commode, mais on ne sait pas ce qui se passe derrière.

Ce parcours tape **chaque commande kubectl une par une** — exactement ce que le `make` fait
en coulisse. Tu verras chaque ressource K8S naître dans le cluster en temps réel.

**Bonus** : pas besoin de compte GHCR. On réutilise l'image buildée à l'étape 13.

### Prérequis : créer le cluster kind

```bash
make k8s-setup
```

Même chose que Parcours 1. ~3 minutes, à faire une seule fois.

> **Note** : la première exécution télécharge ~500 Mo d'images (nginx ingress, cert-manager).
> Prévoir une connexion correcte ou lancer ça avant le cours.

---

### Étape 1 — Construire l'image locale

```bash
docker build -t chatbot-api:local ../etape_13_deployable/
```

> **Pourquoi ce tag `chatbot-api:local` ?**
> C'est un nom arbitraire. On s'en sert à l'étape 2 pour dire à kind "charge cette image-là".

Vérifier que l'image est créée :

```bash
docker images chatbot-api
# chatbot-api   local   a3f8b2c1d4e5   2 minutes ago   287MB
```

---

### Étape 2 — Charger l'image dans le cluster kind

```bash
kind load docker-image chatbot-api:local --name chatbot-local
```

> **Pourquoi cette commande existe-t-elle ?**
> kind fait tourner ton cluster dans des conteneurs Docker.
> Les pods K8S à l'intérieur de ces conteneurs ne voient **pas** les images Docker de ta machine.
> Il faut les transférer explicitement avec `kind load`.
> Sans ça, K8S essaierait de tirer l'image depuis internet → `ErrImagePull`.

Sortie attendue :

```
Image: "chatbot-api:local" with ID "sha256:a3f8b2..." not yet present
on node "chatbot-local-control-plane", loading...
```

---

### Étape 3 — Créer le namespace

```bash
kubectl create namespace chatbot
```

Vérifier :

```bash
kubectl get namespaces
# NAME              STATUS   AGE
# chatbot           Active   3s
# default           Active   4m
# ingress-nginx     Active   3m
# cert-manager      Active   3m
```

> **Pourquoi un namespace ?**
> Un namespace isole les ressources entre elles.
> Tout ce qu'on déploie ira dans `chatbot`.
> Les commandes qui suivent cibleront toujours `-n chatbot`.

---

### Étape 4 — Créer les secrets

```bash
kubectl create secret generic chatbot-secrets \
  --from-literal=openai-api-key="${OPENAI_API_KEY:-sk-fake-local-test}" \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=grafana-password="admin123" \
  -n chatbot
```

Vérifier (les valeurs sont masquées) :

```bash
kubectl describe secret chatbot-secrets -n chatbot
# Name:         chatbot-secrets
# Namespace:    chatbot
# Type:         Opaque
# Data
# ====
# grafana-password:  8 bytes
# openai-api-key:    27 bytes
# secret-key:        64 bytes
```

> **Pourquoi les secrets ne sont pas dans les fichiers YAML du repo ?**
> Les secrets sont encodés en base64, pas chiffrés.
> Les committer dans Git exposerait les clés API.
> C'est pourquoi `k8s/kustomization.yaml` exclut `secret.yaml` intentionnellement.

---

### Étape 5 — Déployer tout le reste

```bash
kubectl apply -k overlays/local-image/
```

> **Pourquoi `-k` et pas `-f` ?**
> `-k` (kustomize) applique un ensemble de fichiers avec des patches.
> L'overlay `overlays/local-image/` réutilise tous les manifests existants
> et applique deux patches sur le Deployment :
> - remplace l'image `ghcr.io/...` par `chatbot-api:local`
> - passe `imagePullPolicy` à `Never` (K8S n'essaie plus de tirer depuis internet)

Ce que tu vois défiler :

```
namespace/chatbot unchanged
configmap/chatbot-config created
persistentvolumeclaim/chatbot-data-pvc created
serviceaccount/chatbot-sa created
deployment.apps/chatbot-api created
service/chatbot-api created
horizontalpodautoscaler.autoscaling/chatbot-api-hpa created
ingress.networking.k8s.io/chatbot-ingress created
deployment.apps/prometheus created
service/prometheus created
deployment.apps/grafana created
service/grafana created
configmap/grafana-provisioning created
```

---

### Étape 6 — Observer le démarrage en direct

Dans un terminal, observe les pods naître :

```bash
kubectl get pods -n chatbot -w
```

```
NAME                            READY   STATUS              RESTARTS   AGE
chatbot-api-7d9f8b6c4-x2k9p     0/1     Pending             0          1s
chatbot-api-7d9f8b6c4-x2k9p     0/1     ContainerCreating   0          2s
chatbot-api-7d9f8b6c4-x2k9p     1/1     Running             0          18s
prometheus-6b8f9c5d7-p4m8q      1/1     Running             0          19s
grafana-5c7d8e9f2-r6n3s         1/1     Running             0          20s
```

`Ctrl+C` pour quitter le mode watch.

> **Les transitions d'état :**
> - `Pending` → K8S a accepté la demande, cherche un nœud
> - `ContainerCreating` → le conteneur démarre
> - `Running` → le conteneur tourne ET les health probes passent
> - `CrashLoopBackOff` → le conteneur plante et K8S le redémarre (voir [diagnostics](#diagnostics))

---

### Étape 7 — Vérifier

```bash
# Statut global
make k8s-status

# Health check direct
curl http://localhost:8080/health

# Confirmer que c'est bien l'image locale (et pas GHCR) qui tourne
kubectl get pod -n chatbot -l app=chatbot-api \
  -o jsonpath='{.items[0].spec.containers[0].image}{"\n"}'
# → chatbot-api:local  ✓
```

Accès :

| Service | URL |
|---|---|
| **API Swagger** | http://localhost:8080/docs |
| **Prometheus** | http://localhost:9090 |
| **Grafana** | http://localhost:3000 — `admin / admin123` |

---

### Diagnostics

Si un pod est en `CrashLoopBackOff` ou `Error` :

```bash
# Voir les events (souvent la cause est là)
kubectl describe pod -n chatbot -l app=chatbot-api

# Logs du conteneur
kubectl logs -n chatbot -l app=chatbot-api

# Logs du crash précédent (si le pod a redémarré)
kubectl logs -n chatbot -l app=chatbot-api --previous
```

Erreur `ErrImageNeverPull` → l'image n'a pas été chargée dans kind. Refaire l'étape 2.

---

### Raccourci : une seule commande

Maintenant que tu as compris chaque étape,
`make deploy-k8s-image` fait exactement la même chose en une commande :

```bash
# Réinitialiser d'abord (si tu as suivi les étapes manuelles)
make k8s-destroy
make k8s-setup

# Puis tout en un :
make deploy-k8s-image
```

Voir la sortie complète : [`output_example/deploy_local_image.log`](output_example/deploy_local_image.log)

### Activer le RAG

Le pod démarre sans base vectorielle — les réponses sont génériques jusqu'à ce que tu indexes les documents.

```bash
make k8s-index-rag
```

Ce que ça fait : lance `scripts/index_rag.py` **à l'intérieur du pod** sur les documents embarqués dans l'image (`/app/docs/`), et écrit la ChromaDB sur le volume persistant (`/app/data/chroma_db/`).

> **Pourquoi le RAG n'est pas automatique au démarrage ?**
> L'indexation prend ~30 secondes (calcul des embeddings) et ne doit se faire qu'une fois.
> Le volume PVC survit aux redémarrages de pods — pas besoin de re-indexer après chaque `make deploy`.

Sortie attendue :

```
INFO: === Indexation RAG ===
INFO: Documents trouvés : 3  (méthode : section)
INFO:   Indexation : entreprise.txt (4832 chars) → 12 chunks
INFO:   Indexation : politique.txt  (3201 chars) →  8 chunks
INFO:   Indexation : technique.txt  (5614 chars) → 14 chunks
INFO: Indexation terminée : 34 chunks dans 'chatbot_docs'

Vérification :
  rag_available: True
```

Voir la sortie complète : [`output_example/make_k8s_index_rag.log`](output_example/make_k8s_index_rag.log)

### Tester les réponses RAG

Une fois le RAG indexé, vérifie que l'API répond correctement aux questions sur TechCorp :

```bash
# Test rapide — 5 questions aléatoires (seuil 60%)
make k8s-smoke

# Test complet — 15 questions avec réponses détaillées (seuil 70%)
make k8s-eval-verbose
```

Score attendu : ≥ 12/15 PASS (80%).
Voir un exemple de résultat : [`output_example/make_k8s_eval_verbose.log`](output_example/make_k8s_eval_verbose.log)

### Nettoyage

```bash
make k8s-destroy
```

---

## Parcours 1 — Je découvre Kubernetes

### Qu'est-ce que Kubernetes ?

Docker Compose gère des conteneurs sur **une seule machine**.
Kubernetes (K8S) gère des conteneurs sur **plusieurs machines** (un cluster).

En production, les applications tournent sur des clusters K8S qui gèrent automatiquement :

- Le redémarrage si un conteneur crash (**self-healing**)
- La montée en charge si le trafic augmente (**autoscaling**)
- Les mises à jour sans interruption de service (**rolling update**)

**kind** (Kubernetes IN Docker) simule un cluster K8S complet dans des conteneurs Docker,
sur ta machine. Tu obtiens une expérience identique à un vrai cluster GKE (Google Kubernetes Engine de GCP)/EKS (Amazon Elastic Kubernetes Service) /AKS (Azure Kubernetes Engine)

### Architecture du cluster

```
Ta machine
  └── Docker
        └── kind-control-plane   ← seul nœud (fait aussi worker en local)
              └── chatbot-api pod   ← ton application (1 à 10 replicas)
              └── prometheus pod
              └── grafana pod
```

### Prérequis

Ces commandes installent des binaires système — à lancer **depuis n'importe quel répertoire**
(comme installer docker ou curl, aucun lien avec le projet) :

```bash
# kind — Kubernetes local dans Docker
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# kubectl — outil en ligne de commande pour parler au cluster
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/kubectl

# Vérifier
kind version && kubectl version --client
```

Une fois installés, toutes les commandes `make` du Parcours 1 se lancent depuis `etape_14_deployed/` :

```bash
cd etape_14_deployed/
make k8s-setup
make deploy-k8s-local
```

### Étape 1 — Créer le cluster

```bash
make k8s-setup
```

Ce que ça fait :

- Crée un cluster kind avec 1 control-plane + 2 workers
- Installe Nginx Ingress Controller (pour exposer l'API sur localhost:8080)
- Configure cert-manager (TLS local)

Durée : ~3 minutes (téléchargements).

### Étape 2 — Déployer l'application

```bash
make deploy-k8s-local
```

Ce que ça fait :

- Injecte les variables du `.env` dans le ConfigMap K8S (MODE, LOCAL_BASE_URL, LOCAL_MODEL)
- Crée le namespace `chatbot` et le secret GHCR pour puller l'image
- Applique tous les manifests K8S (chatbot + Prometheus + Grafana)
- K8S tire l'image directement depuis GHCR (`ghcr.io/fabienquimper/chatbot-api:latest`)
- Attend que les pods soient `Running`

> **Prérequis** : `REGISTRY_USER` et `REGISTRY_TOKEN` doivent être dans le `.env`
> (copiés depuis l'étape 13 — `cp ../etape_13_deployable/.env .env`)

### Étape 3 — Activer le RAG

```bash
make k8s-index-rag
```

Sans cette étape, l'API répond mais ignore les documents internes — les réponses sont génériques.

Voir la sortie complète : [`output_example/make_k8s_index_rag.log`](output_example/make_k8s_index_rag.log)

### Étape 4 — Tester le RAG

Vérifie que l'API répond correctement aux questions sur TechCorp :

```bash
# Test rapide — 5 questions aléatoires
make k8s-smoke

# Test complet — 15 questions avec réponses complètes affichées
make k8s-eval-verbose
```

Score attendu : ≥ 12/15 PASS (80%).

```
═══════════════════════════════════════════════════════════════
  Résultat : 12/15 PASS (80%)   1 PARTIEL   2 FAIL
  Latence  : moy=2.07s  min=1.28s  max=3.92s

  Catégorie            Pass  Score
  company             3/3  ██████████ 100%
  pricing             2/2  ██████████ 100%
  rgpd                2/2  ██████████ 100%
  securite            1/1  ██████████ 100%
  sla                 0/1  █████░░░░░ 50%
  support             1/2  █████░░░░░ 50%
  technique           3/4  ███████░░░ 75%
═══════════════════════════════════════════════════════════════
```

Voir la sortie complète avec toutes les réponses : [`output_example/make_k8s_eval_verbose.log`](output_example/make_k8s_eval_verbose.log)

### Étape 5 — Vérifier

```bash
make k8s-status

# Ou directement avec kubectl
kubectl get pods -n chatbot
```

Si un pod est en `CrashLoopBackOff` ou `Error`, diagnostiquer ainsi :

```bash
# Voir l'état en temps réel
kubectl get pods -n chatbot -w

# Détail des erreurs d'un pod
kubectl describe pod -n chatbot -l app=chatbot-api

# Logs du pod (ou de l'initContainer s'il y en a un)
kubectl logs -n chatbot -l app=chatbot-api
kubectl logs -n chatbot -l app=chatbot-api --previous   # logs du crash précédent
```

Sortie attendue :

```
NAME                           READY   STATUS    RESTARTS
chatbot-api-7d9f8b6c4-x2k9p    1/1     Running   0
prometheus-6b8f9c5d7-p4m8q     1/1     Running   0
grafana-5c7d8e9f2-r6n3s        1/1     Running   0
```

Accès — tous les services sont directement accessibles comme à l'étape 13 :


| Service          | URL                          | Identifiants     |
| ---------------- | ---------------------------- | ---------------- |
| **API Swagger**  | http://localhost:8080/docs   | —               |
| **Health check** | http://localhost:8080/health | —               |
| **Prometheus**   | http://localhost:9090        | —               |
| **Grafana**      | http://localhost:3000        | admin / admin123 |

> Prometheus et Grafana sont exposés via NodePort (ports 30030 et 30090 dans le cluster,
> mappés sur 3000 et 9090 sur ta machine). Pas besoin de `port-forward`.

### Étape 6 — Explorer le cluster (tuto interactif)

Kubernetes expose tout via des **ressources**. Voici comment les inspecter une par une.
Lance chaque commande et observe ce qu'elle retourne — c'est comme ça qu'on apprend K8S.

---

#### Pods — l'unité de base

Un **pod** est un ou plusieurs conteneurs qui tournent ensemble sur un nœud.

```bash
# Lister les pods du namespace chatbot
kubectl get pods -n chatbot

# Même chose mais avec plus d'infos (nœud, IP interne)
kubectl get pods -n chatbot -o wide

# Voir les pods de TOUS les namespaces
kubectl get pods -A

# Regarder un pod en temps réel (Ctrl+C pour quitter)
kubectl get pods -n chatbot -w

# Détail complet d'un pod : events, volumes, variables d'env, état des conteneurs
kubectl describe pod -n chatbot -l app=chatbot-api

# Logs du pod en direct
kubectl logs -f deployment/chatbot-api -n chatbot

# Logs du crash précédent (si le pod a redémarré)
kubectl logs -n chatbot -l app=chatbot-api --previous

# Ouvrir un shell dans le pod (comme docker exec)
kubectl exec -it deployment/chatbot-api -n chatbot -- /bin/sh
```

---

#### Deployments — ce qui gère les pods

Un **Deployment** déclare combien de replicas doivent tourner et quelle image utiliser.
K8S s'assure en permanence que l'état réel = l'état déclaré.

```bash
# Lister les deployments
kubectl get deployments -n chatbot

# Détail d'un deployment
kubectl describe deployment chatbot-api -n chatbot

# Historique des versions déployées
kubectl rollout history deployment/chatbot-api -n chatbot

# Scaler manuellement à 2 replicas
kubectl scale deployment chatbot-api --replicas=2 -n chatbot

# Revenir à 1
kubectl scale deployment chatbot-api --replicas=1 -n chatbot

# Rollback vers la version précédente
kubectl rollout undo deployment/chatbot-api -n chatbot

# Voir le statut du rollout en cours
kubectl rollout status deployment/chatbot-api -n chatbot
```

---

#### Self-healing — K8S recrée les pods supprimés

```bash
# Dans un terminal : observer les pods en temps réel
kubectl get pods -n chatbot -w

# Dans un autre terminal : supprimer un pod
kubectl delete pod -l app=chatbot-api -n chatbot

# → K8S détecte la disparition et recrée le pod automatiquement
```

---

#### Services — le réseau interne

Un **Service** expose un Deployment à l'intérieur du cluster (load balancing entre les pods).

```bash
# Lister les services
kubectl get services -n chatbot

# Détail d'un service (ports, sélecteur de pods, endpoints)
kubectl describe service chatbot-api -n chatbot
```

---

#### Ingress — l'exposition vers l'extérieur

L'**Ingress** est le point d'entrée HTTP depuis ta machine vers le cluster.
C'est lui qui route `localhost:8080` vers le service `chatbot-api`.

```bash
# Voir la règle d'ingress
kubectl get ingress -n chatbot

# Détail : host, path, service cible
kubectl describe ingress chatbot-ingress -n chatbot
```

---

#### ConfigMaps — la configuration

Un **ConfigMap** stocke des variables de configuration (non-secrètes) injectées dans les pods.

```bash
# Lister les configmaps
kubectl get configmap -n chatbot

# Voir le contenu du configmap de l'app
kubectl get configmap chatbot-config -n chatbot -o yaml
```

---

#### Secrets — les données sensibles

Un **Secret** stocke des données sensibles (API keys, mots de passe) encodées en base64.

```bash
# Lister les secrets
kubectl get secrets -n chatbot

# Voir les clés d'un secret (les valeurs sont masquées)
kubectl describe secret chatbot-secrets -n chatbot

# Décoder une valeur (à faire avec prudence !)
kubectl get secret chatbot-secrets -n chatbot \
  -o jsonpath='{.data.grafana-password}' | base64 -d; echo
```

---

#### HPA — l'autoscaling

Le **HorizontalPodAutoscaler** ajoute ou supprime des pods selon la charge CPU/mémoire.

```bash
# L'app tourne avec minimum 1 replica (configuré dans k8s/chatbot-hpa.yaml)
# Le HPA peut monter jusqu'à 10 replicas si CPU > 70% ou mémoire > 80%
kubectl get hpa -n chatbot

# Détail : seuils de déclenchement, politique de scale
kubectl describe hpa chatbot-api-hpa -n chatbot

# Scaler manuellement à 3 replicas (simulation de charge)
kubectl scale deployment chatbot-api --replicas=3 -n chatbot
kubectl get pods -n chatbot   # → 3 pods Running

# Revenir à 1
kubectl scale deployment chatbot-api --replicas=1 -n chatbot
```

---

#### Namespaces — l'isolation

Un **Namespace** est un espace de noms qui isole les ressources.
Tout ce qui tourne dans le namespace `chatbot` n'est pas visible depuis `ingress-nginx`.

```bash
# Lister les namespaces du cluster
kubectl get namespaces

# Voir toutes les ressources d'un namespace d'un coup
kubectl get all -n chatbot
kubectl get all -n ingress-nginx
kubectl get all -n cert-manager
```

---

#### Nœuds — la machine sous-jacente

```bash
# Voir les nœuds du cluster et leur état
kubectl get nodes

# Ressources disponibles sur le nœud (CPU, mémoire)
kubectl describe node chatbot-local-control-plane | grep -A10 "Allocated resources"
```

### Nettoyage

```bash
make k8s-destroy   # supprime le cluster kind
```

---

## Parcours 2 — Pipeline de release complet

### Ce que ça simule

En entreprise, personne ne déploie manuellement. Le processus est :

```
Développeur
    │ git tag release0001
    ▼
┌─────────┐       ┌──────────────────────┐
│  Gitea  │──────▶│  CI (act)            │  lint + tests + docker build
│  :3001  │       │  GitHub Actions local│  push image → registry local
│  (=GitHub)      └──────────────────────┘
└─────────┘                 │
                            ▼
                  ┌──────────────────────┐
                  │  Registry local      │  :5001  (= GHCR en local)
                  └──────────────────────┘
                            │
                            ▼
                  ┌──────────────────────┐
                  │  ArgoCD              │  Détecte le nouveau tag
                  │  (dans kind)         │  Déploie automatiquement
                  └──────────────────────┘
                            │
                            ▼
                  ┌──────────────────────┐
                  │  kind (K8S local)    │  Nouvelle version en ligne
                  │  chatbot-api pods    │  sans interruption de service
                  └──────────────────────┘
```

### Chaque composant, son rôle


| Composant          | Rôle                                             | Équivalent en prod    |
| ------------------ | ------------------------------------------------- | ---------------------- |
| **Gitea** :3001    | Serveur Git auto-hébergé                        | GitHub                 |
| **act**            | Exécute les workflows GitHub Actions en local    | GitHub Actions runners |
| **Registry :5001** | Stocke les images Docker                          | ghcr.io                |
| **kind**           | Cluster Kubernetes local                          | GKE / EKS / AKS        |
| **ArgoCD** :8081   | Surveille le repo Git et déploie automatiquement | ArgoCD en prod         |

> L'architecture est **identique** à la production — seules les URLs changent.
> Un manifest K8S validé ici fonctionnera sur GKE sans modification.

### Prérequis supplémentaires

En plus de kind et kubectl (installés au Parcours 1) :

```bash
# act — exécute GitHub Actions en local
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
act --version

# argocd CLI (optionnel — l'UI web suffit)
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd && sudo mv argocd /usr/local/bin/argocd
```

### Étape 1 — Installer le pipeline complet

```bash
./scripts/setup-local-pipeline.sh setup
```

Ce script installe et configure automatiquement :

- Registry Docker local (port 5001)
- Gitea (port 3001) avec compte admin créé automatiquement
- Cluster kind connecté au registry local
- ArgoCD dans le cluster

Durée : ~5 minutes.

À la fin, le script affiche les URLs et les étapes suivantes.

### Étape 2 — Configurer Gitea

```bash
# 1. Ouvrir http://localhost:3001
# 2. Se connecter : admin / admin1234
# 3. Créer un repo "chatbot-api" (bouton "+" → Nouveau dépôt, public, sans init)

# 4. Ajouter le remote local
git remote add local http://localhost:3001/admin/chatbot-api.git
git push local main
# → Login : admin / admin1234
```

### Étape 3 — Configurer les secrets CI

```bash
cp .secrets.act.example .secrets.act
# Éditer .secrets.act si nécessaire (OPENAI_API_KEY pour les tests)
```

### Étape 4 — Créer le secret K8S (une seule fois)

```bash
kubectl create namespace chatbot 2>/dev/null || true

kubectl create secret generic chatbot-secrets \
  --from-literal=openai-api-key="${OPENAI_API_KEY:-sk-fake-local-test}" \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=grafana-password="admin123" \
  -n chatbot \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Étape 5 — Configurer ArgoCD

```bash
# Appliquer l'Application ArgoCD (pointe vers Gitea)
kubectl apply -f k8s/argocd/application.yaml

# Accéder à l'UI ArgoCD (dans un terminal séparé)
kubectl port-forward svc/argocd-server -n argocd 8081:443 &

# Récupérer le mot de passe admin
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

Ouvrir https://localhost:8081 (accepter le certificat auto-signé).
Login : `admin` / mot de passe affiché ci-dessus.

### Étape 6 — Déclencher une release

C'est ici que tout s'assemble. Un tag git déclenche le pipeline complet :

```bash
# Faire un changement dans le code
echo "# release0001" >> ../etape_13_deployable/app/main.py

# Committer et tagger
git add .
git commit -m "release0001"
git tag release0001
git push local main --tags
```

Ce qui se passe automatiquement :

1. **act** détecte le push → lance `ci.yml` (lint + tests + docker build)
2. Si CI passe → build l'image et push vers `localhost:5001/chatbot-api:release0001`
3. **ArgoCD** détecte le nouveau tag → applique les manifests K8S mis à jour
4. K8S fait un **rolling update** : nouveaux pods démarrés avant les anciens arrêtés

Voir le déploiement en temps réel dans l'UI ArgoCD ou avec :

```bash
kubectl get pods -n chatbot -w
```

### Workflow quotidien

```bash
# 1. Modifier le code
vim ../etape_13_deployable/app/main.py

# 2. Lancer le CI local (lint + tests)
./scripts/setup-local-pipeline.sh ci

# 3. Builder et pusher l'image vers le registry local
./scripts/setup-local-pipeline.sh push-image

# 4. Pousser le code sur Gitea
git push local main

# 5. Voir ArgoCD déployer automatiquement
kubectl get pods -n chatbot -w
# Ou via UI : https://localhost:8081

# 6. Forcer une sync si nécessaire
./scripts/setup-local-pipeline.sh sync
```

### Statut global du pipeline

```bash
./scripts/setup-local-pipeline.sh status
```

Affiche l'état de chaque composant : registry, Gitea, cluster, pods, ArgoCD.

### Nettoyage

```bash
# Supprimer tout (cluster + registry + Gitea)
./scripts/setup-local-pipeline.sh destroy

# Garder le cluster mais supprimer registry + Gitea
kind delete cluster --name chatbot-pipeline
```

---

## Commandes Makefile

```bash
make help   # liste toutes les commandes
```


| Commande                | Description                             |
| ----------------------- | --------------------------------------- |
| `make registry-ls`      | Liste les versions sur ghcr.io          |
| `make test-registry`    | Teste l'authentification sur ghcr.io    |
|                         |                                         |
| `make pull`             | Télécharge l'image depuis ghcr.io     |
| `make deploy-local`     | Lance la stack depuis GHCR (sans K8S)   |
| `make deploy-vps`       | Déploie sur un serveur distant via SSH |
|                         |                                         |
| `make k8s-setup`         | Crée le cluster kind                          |
| `make deploy-k8s-image`  | Build image locale + déploie (Parcours 0)     |
| `make deploy-k8s-local`  | Déploie depuis GHCR dans le cluster kind      |
| `make k8s-index-rag`     | Indexe les documents RAG dans le pod          |
| `make k8s-smoke`         | 5 questions aléatoires — vérifie le RAG       |
| `make k8s-eval`          | 15 questions avec score (seuil 70%)           |
| `make k8s-eval-verbose`  | Idem avec les réponses complètes              |
| `make k8s-status`        | Statut du cluster                             |
| `make k8s-destroy`       | Supprime le cluster                           |
|                         |                                         |
| `make status`           | Statut des conteneurs + health check    |
| `make logs`             | Logs de l'API                           |
| `make stop`             | Arrête la stack Docker Compose         |
| `make clean`            | Arrête et supprime les volumes         |

---

## CI/CD GitHub Actions (le vrai, sur GitHub)

Les fichiers `.github/workflows/` sont prêts pour GitHub — ils font la même chose que
le Parcours 2 mais sur de vrais serveurs GitHub.

### Pipeline configuré

```
Push / PR  →  ci.yml
               ├── ruff (lint Python)
               ├── pytest (coverage ≥ 70%)
               ├── bandit + safety (sécurité)
               └── docker build (validation)

Merge main →  cd.yml
               ├── Tests obligatoires
               ├── Build + Push → ghcr.io/.../chatbot-api:sha
               └── Deploy → Staging (SSH automatique)

Tag v*.*.* →  cd.yml (suite)
               └── Deploy → Production

Hebdomadaire → security.yml
               ├── Safety (dépendances Python)
               └── Trivy (scan de l'image Docker)
```

### Secrets à configurer sur GitHub

Dans `Settings → Secrets and variables → Actions` :


| Secret            | Description           |
| ----------------- | --------------------- |
| `STAGING_HOST`    | IP du serveur staging |
| `STAGING_USER`    | Utilisateur SSH       |
| `STAGING_SSH_KEY` | Clé privée SSH      |
| `PROD_HOST`       | IP serveur production |
| `PROD_USER`       | Utilisateur SSH prod  |
| `PROD_SSH_KEY`    | Clé privée SSH prod |

> `GITHUB_TOKEN` est automatiquement fourni par GitHub — pas à configurer.

---

## Pour aller plus loin

- **Google Cloud** (Cloud Run serverless ou GKE) → [docs/DEPLOY_GCP.md](docs/DEPLOY_GCP.md)
- **AWS** (ECS Fargate ou EKS) → [docs/DEPLOY_AWS.md](docs/DEPLOY_AWS.md)
- **Kubernetes local détaillé** (rollback, HPA, ingress) → [docs/DEPLOY_LOCAL_K8S.md](docs/DEPLOY_LOCAL_K8S.md)
- **Pipeline local complet** (tous les détails ArgoCD + webhooks) → [docs/LOCAL_PIPELINE.md](docs/LOCAL_PIPELINE.md)
