# Déploiement sur Amazon Web Services

Deux options : **ECS Fargate** (serverless containers) ou **EKS** (Kubernetes managé).

---

## Option 1 — ECS Fargate (recommandé pour démarrer)

Fargate exécute vos containers sans gérer d'instances EC2.

### Prérequis

```bash
# Installer AWS CLI
# https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

aws configure
# AWS Access Key ID: ...
# Default region name: eu-west-3
# Default output format: json
```

### Étapes

#### 1. Registry ECR

```bash
AWS_REGION="eu-west-3"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/chatbot-api"

# Créer le repo
aws ecr create-repository \
  --repository-name chatbot-api \
  --region "${AWS_REGION}" \
  --image-scanning-configuration scanOnPush=true

# Authentification Docker
aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS \
  --password-stdin "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
```

#### 2. Build et push

```bash
docker build --target production \
  -t "${ECR_REPO}:latest" \
  etape_13_deployable/

docker push "${ECR_REPO}:latest"
```

#### 3. Secrets dans AWS Secrets Manager

```bash
# Créer les secrets
aws secretsmanager create-secret \
  --name chatbot/openai-api-key \
  --secret-string "sk-your-openai-key" \
  --region "${AWS_REGION}"

aws secretsmanager create-secret \
  --name chatbot/secret-key \
  --secret-string "$(openssl rand -hex 32)" \
  --region "${AWS_REGION}"
```

#### 4. Task Definition ECS

```bash
# Créer le fichier task-definition.json
cat > /tmp/chatbot-task.json << EOF
{
  "family": "chatbot-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT}:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "chatbot",
      "image": "${ECR_REPO}:latest",
      "portMappings": [
        {"containerPort": 8000, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "MODEL", "value": "gpt-4o-mini"},
        {"name": "MODE", "value": "cloud"},
        {"name": "DB_PATH", "value": "/app/data/chat.db"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:chatbot/openai-api-key"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:chatbot/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/chatbot-api",
          "awslogs-region": "${AWS_REGION}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 10,
        "retries": 3
      }
    }
  ]
}
EOF

aws ecs register-task-definition \
  --cli-input-json file:///tmp/chatbot-task.json \
  --region "${AWS_REGION}"
```

#### 5. Service ECS avec ALB

```bash
# Créer le service ECS
aws ecs create-service \
  --cluster chatbot-cluster \
  --service-name chatbot-api \
  --task-definition chatbot-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-xxx,subnet-yyy],
    securityGroups=[sg-xxx],
    assignPublicIp=ENABLED
  }" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=chatbot,containerPort=8000" \
  --health-check-grace-period-seconds 30 \
  --region "${AWS_REGION}"
```

#### 6. Auto-scaling

```bash
# Enregistrer la cible de scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/chatbot-cluster/chatbot-api \
  --min-capacity 2 \
  --max-capacity 10

# Politique de scaling sur CPU
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/chatbot-cluster/chatbot-api \
  --policy-name chatbot-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 30
  }'
```

---

## Option 2 — EKS (Elastic Kubernetes Service)

```bash
# Créer le cluster EKS (avec eksctl)
eksctl create cluster \
  --name chatbot-cluster \
  --region eu-west-3 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed

# Configurer kubectl
aws eks update-kubeconfig \
  --region eu-west-3 \
  --name chatbot-cluster

# Installer AWS Load Balancer Controller
# https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html

# Déployer avec les manifests K8S
cd etape_14_deployed/k8s
IMAGE="${ECR_REPO}:latest"
sed -i "s|ghcr.io/YOUR_ORG/chatbot-api|${IMAGE}|g" \
  chatbot-deployment.yaml kustomization.yaml

kubectl apply -k .
```

---

## Monitoring AWS

```bash
# CloudWatch Container Insights
aws ecs put-account-setting-default \
  --name containerInsights \
  --value enabled

# Métriques Prometheus → Amazon Managed Prometheus (AMP)
# https://docs.aws.amazon.com/prometheus/latest/userguide/

aws amp create-workspace \
  --alias chatbot-monitoring \
  --region "${AWS_REGION}"
```

---

## Estimation des coûts (eu-west-3 / Paris)

| Service | Configuration | Coût estimé/mois |
|---|---|---|
| ECS Fargate | 2 tâches, 0.5 vCPU/1GB | ~25-40€ |
| ECR | ~1GB images stockées | ~0.10€ |
| ALB | Application Load Balancer | ~20-25€ |
| Secrets Manager | 2 secrets | ~0.80€ |
| CloudWatch Logs | ~5GB/mois | ~2-5€ |
| EKS | Cluster managé + 2 nodes t3.medium | ~120-150€ |

> Utiliser le [calculateur AWS](https://calculator.aws/).
> Activer AWS Cost Anomaly Detection pour éviter les mauvaises surprises.
