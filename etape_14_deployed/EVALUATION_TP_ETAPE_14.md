# 🧠 Évaluation — Étape 14 : Deployed (Kubernetes & CI/CD)

> ⏱ Durée estimée : 90-120 min | Niveau : Avancé

## 🎯 Enjeu central

"L'application est prête — où et comment on la déploie ?"
Cette étape propose 3 parcours : image locale dans kind (rapide), pull depuis GHCR (réaliste),
pipeline GitOps complet avec ArgoCD (niveau production).
L'enjeu : comprendre ce que Kubernetes apporte (autoscaling, rollback, orchestration)
et ce qu'il coûte (complexité opérationnelle).

```
Parcours 0 → image locale + kubectl à la main       ⏱ ~20 min  ⭐ (recommandé)
Parcours 1 → image GHCR + cluster kind              ⏱ ~30 min
Parcours 2 → GitOps complet (Gitea + ArgoCD + act)  ⏱ ~2h
```

---

## ✅ Checklist de validation

- [ ] J'ai créé le cluster kind avec `make k8s-setup`
- [ ] J'ai déployé le chatbot (Parcours 0 ou 1)
- [ ] `curl http://localhost:8080/health` répond correctement
- [ ] J'ai inspecté les pods avec `kubectl get pods -n chatbot`
- [ ] J'ai effectué un scaling manuel et observé les pods se créer/détruire

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Après `kubectl apply -k etape_14_deployed/k8s/`, liste tous les pods en cours dans le namespace `chatbot`. Quel est leur statut ?

   > _________________________________________________________

2. Quelle commande as-tu utilisée pour charger l'image locale dans kind ? Pourquoi cette étape est-elle nécessaire ?

   > _________________________________________________________

3. Après `kubectl scale deployment chatbot-api --replicas=3 -n chatbot`, combien de pods apparaissent ? En combien de secondes sont-ils `Running` ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. L'HPA scale de 1 à 10 replicas sur CPU > 70% et RAM > 80%. Pourquoi le scaling **CPU** déclenche avant le **RAM** pour un chatbot sous charge ? Que se passe-t-il pour les requêtes en cours pendant un scale-down ?

   > _________________________________________________________

2. ArgoCD surveille le repo Git et synchronise automatiquement. Explique la différence entre le modèle **GitOps** (ArgoCD) et le modèle **push traditionnel** (script SSH). Quels avantages concrètement pour une équipe de 5 devs ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Incident en prod : la dernière mise à jour a cassé le chatbot. Rollback en moins de 2 minutes. Décris la procédure exacte avec les commandes K8S. Y a-t-il interruption de service ?

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Lance `kubectl rollout history deployment/chatbot-api -n chatbot`.
Effectue un changement fictif (variable d'environnement dans le manifest), applique-le,
puis rollback avec `kubectl rollout undo`.
Le service est-il interrompu pendant l'opération ?

**Nombre de révisions dans l'historique :** `_______`

**Service interrompu ? (oui/non) :** `_______`

**Explication :**
```
_____________________________________________________________
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Déploiement** : Comparez les 3 stratégies (Docker Compose VPS, Kubernetes kind, Cloud Run) pour un chatbot d'entreprise avec 200 utilisateurs. Quels critères décisionnels (coût, compétences, SLA, scalabilité) ?
- **CI/CD** : Décrivez le flux complet depuis un `git push` jusqu'au pod Kubernetes mis à jour, en nommant chaque composant (GitHub Actions, GHCR, ArgoCD, kind). Identifiez les points de contrôle qualité.
- **Prévention des risques** : L'HPA peut scaler jusqu'à 10 replicas. Quel risque côté coût et côté quota LLM ? Proposez une stratégie de protection (circuit breaker, quota, alertes de coût).

---

## 💡 Pour aller plus loin

- Parcours 2 : configure Gitea + ArgoCD et observe la synchronisation automatique après un `git push`.
- Modifie `maxReplicas` à 3 dans `chatbot-hpa.yaml` et génère de la charge avec Locust. Observe l'HPA avec `kubectl get hpa -n chatbot -w`.
- Cherche la différence entre **Rolling Update** (défaut K8S) et **Blue/Green Deployment**.
