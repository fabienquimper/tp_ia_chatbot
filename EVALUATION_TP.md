# Évaluation TP — Chatbot IA : du prototype au déploiement

> **Bloc CCP4 — Chef de Projet IA**

Ce document est le point d'entrée des évaluations formatives du TP.
Chaque étape a son propre fichier `EVALUATION_TP_ETAPE_XX.md` dans son dossier.

**Règle d'or :** Lis le fichier d'évaluation **après** avoir exécuté l'étape, pas avant.
Les questions de niveau 1 sont impossibles à répondre sans avoir lancé le code — c'est voulu.

---

## Philosophie du TP

Une app IA, c'est avant tout **un logiciel à déployer, mesurer et sécuriser**.
L'objectif n'est pas de produire du code parfait, mais de comprendre ce qui se passe,
pourquoi ça marche (ou pas), et ce que cela implique en production.

Les évaluations suivent 3 niveaux de questionnement :
- **Niveau 1 — Observation** : tu as vu, tu peux répondre (impossible sans exécuter)
- **Niveau 2 — Analyse** : tu comprends pourquoi le mécanisme fonctionne
- **Niveau 3 — Décision** : tu ferais quoi en production, en tant que chef de projet ?

---

## Progression et fichiers d'évaluation

| Étape | Thème | Niveau | Durée | Fichier |
|-------|-------|--------|-------|---------|
| 00 | Le Moteur — connexion LLM, variables d'env | Débutant | 30 min | [etape_00_moteur/EVALUATION_TP_ETAPE_00.md](etape_00_moteur/EVALUATION_TP_ETAPE_00.md) |
| 01 | Le Chatbot Naïf — stateless, mémoire côté client | Débutant | 30 min | [etape_01_banane/EVALUATION_TP_ETAPE_01.md](etape_01_banane/EVALUATION_TP_ETAPE_01.md) |
| 02 | KPIs — latence, TPS, coût, P95 | Débutant | 30 min | [etape_02_kpis/EVALUATION_TP_ETAPE_02.md](etape_02_kpis/EVALUATION_TP_ETAPE_02.md) |
| 03 | Mémoire Tampon — fenêtre glissante, résumé | Intermédiaire | 45 min | [etape_03_memoire/EVALUATION_TP_ETAPE_03.md](etape_03_memoire/EVALUATION_TP_ETAPE_03.md) |
| 04 | Persistance — SQLite vs JSON, sessions | Intermédiaire | 45 min | [etape_04_persistance/EVALUATION_TP_ETAPE_04.md](etape_04_persistance/EVALUATION_TP_ETAPE_04.md) |
| 05 | RAG — ChromaDB, embeddings, hit rate | Intermédiaire | 60 min | [etape_05_rag/EVALUATION_TP_ETAPE_05.md](etape_05_rag/EVALUATION_TP_ETAPE_05.md) |
| 06 | LangChain — abstraction, swap cloud/local | Intermédiaire | 45 min | [etape_06_langchain/EVALUATION_TP_ETAPE_06.md](etape_06_langchain/EVALUATION_TP_ETAPE_06.md) |
| 07 | Docker & FastAPI — API REST, containerisation | Intermédiaire | 60 min | [etape_07_docker/EVALUATION_TP_ETAPE_07.md](etape_07_docker/EVALUATION_TP_ETAPE_07.md) |
| 08 | Monitoring — Prometheus, Grafana, PromQL | Intermédiaire | 60 min | [etape_08_monitoring/EVALUATION_TP_ETAPE_08.md](etape_08_monitoring/EVALUATION_TP_ETAPE_08.md) |
| 09 | Sécurité — JWT, rate limiting, injection prompt | Avancé | 60 min | [etape_09_securite/EVALUATION_TP_ETAPE_09.md](etape_09_securite/EVALUATION_TP_ETAPE_09.md) |
| 10 | Test de charge — Locust, SLA, goulots | Avancé | 60 min | [etape_10_locust/EVALUATION_TP_ETAPE_10.md](etape_10_locust/EVALUATION_TP_ETAPE_10.md) |
| 11 | Tests automatisés — pytest, mock, coverage | Avancé | 60 min | [etape_11_tests/EVALUATION_TP_ETAPE_11.md](etape_11_tests/EVALUATION_TP_ETAPE_11.md) |
| 12 | Benchmark — LLM-as-Judge, qualité/prix | Avancé | 60 min | [etape_12_benchmark/EVALUATION_TP_ETAPE_12.md](etape_12_benchmark/EVALUATION_TP_ETAPE_12.md) |
| 13 | Production-Ready — Dockerfile multi-stage, stack complète | Avancé | 90 min | [etape_13_deployable/EVALUATION_TP_ETAPE_13.md](etape_13_deployable/EVALUATION_TP_ETAPE_13.md) |
| 14 | Deployed — Kubernetes, CI/CD, GitOps | Avancé | 90-120 min | [etape_14_deployed/EVALUATION_TP_ETAPE_14.md](etape_14_deployed/EVALUATION_TP_ETAPE_14.md) |

---

## Arc narratif du TP

```
00 → "Le LLM ne se souvient de rien — comment construire une mémoire ?"
03 → "La mémoire a un coût — comment l'optimiser ?"
05 → "Le LLM ne sait que ce qu'on lui donne — RAG comme mémoire externe"
07 → "Le chatbot devient un service — comment l'exposer ?"
08 → "On ne peut pas corriger ce qu'on ne voit pas — métriques"
09 → "Un service exposé est une cible — sécurité en profondeur"
10 → "Est-ce que ça tient la charge ? — test de limite"
11 → "Est-ce qu'on peut livrer en confiance ? — tests automatisés"
13 → "Toutes les briques ensemble — prêt pour la prod"
14 → "La prod, c'est quoi concrètement ? — CI/CD + K8S + GitOps"
```

---

## Lien avec le dossier E8

Chaque fichier d'évaluation contient une section **"Lien avec le dossier E8"**.
Ces questions sont directement réutilisables dans les parties :
- Développement et choix d'architecture
- Tests et validation
- Déploiement et mise en production
- Prévention des risques
- Aspects réglementaires (RGPD, sécurité)
