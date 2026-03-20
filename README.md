# TP IA — Construction d'un Chatbot de A à Z

Bienvenue dans ce TP pratique (Travaux Pratiques) sur la construction d'un chatbot IA complet.
Vous allez partir d'un simple script Python de 10 lignes et arriver à une API sécurisée,
monitorée, testée et benchmarkée.

---

## Vue d'ensemble du projet

```
tp_ia_chatbot/
├── etape_00_moteur/        # Connexion au LLM (cloud ou local)
├── etape_01_banane/        # Chatbot naïf — le problème d'amnésie
├── etape_02_kpis/          # Mesurer latence, TPS, coût
├── etape_03_memoire/       # Fenêtre glissante + résumé automatique
├── etape_04_persistance/   # SQLite et JSON — sauvegarder les sessions
├── etape_05_rag/           # RAG avec ChromaDB — grounding dans vos docs
├── etape_06_langchain/     # LangChain — framework d'orchestration
├── etape_07_docker/        # API FastAPI dockerisée
├── etape_08_monitoring/    # Prometheus + Grafana
├── etape_09_securite/      # JWT, rate limiting, sanitisation
├── etape_10_locust/        # Tests de charge avec Locust
├── etape_11_tests/         # Tests unitaires, intégration, E2E
└── etape_12_benchmark/     # Benchmark LLM-as-Judge
```

---

## Prérequis

| Outil | Version minimale | Utilisation |
|-------|-----------------|-------------|
| Python | 3.11+ | Langage principal |
| pip | 23+ | Gestion des dépendances |
| Docker | 24+ | Étapes 07, 08, 09 |
| Docker Compose | 2.0+ | Orchestration des services |
| LM Studio | optionnel | Modèle local (étape 00) |

### Clé API OpenAI (recommandée)

Les étapes utilisent par défaut l'API OpenAI. Créez un compte sur [platform.openai.com](https://platform.openai.com), générez une clé API, et gardez-la sous la main.

### Alternative locale avec LM Studio

Si vous n'avez pas de clé OpenAI, installez [LM Studio](https://lmstudio.ai/), téléchargez un modèle (ex: `mistral-7b-instruct`), démarrez le serveur local sur `http://localhost:1234`, et configurez `MODE=local` dans votre `.env`.

---

## Installation rapide

```bash
# Cloner / naviguer dans le projet
cd tp_ia_chatbot

# Chaque étape est autonome — exemple pour l'étape 01 :
cd etape_01_banane
cp .env.example .env
# Éditez .env et ajoutez votre clé OPENAI_API_KEY
pip install -r requirements.txt
python chatbot_naif.py
```

---

## Progression des étapes

### Étape 00 — Le Moteur
**Objectif :** Établir la connexion avec le LLM (cloud OpenAI ou local LM Studio).
**Ce que vous apprenez :** API OpenAI, variables d'environnement, dotenv.

### Étape 01 — Le Chatbot Naïf (La Banane)
**Objectif :** Créer un chatbot fonctionnel en ~10 lignes. Constater l'amnésie.
**Ce que vous apprenez :** La nature stateless des LLMs, le rôle de l'historique côté client.

### Étape 02 — Les KPIs
**Objectif :** Mesurer latence, tokens par seconde, coût estimé.
**Ce que vous apprenez :** Métriques de performance LLM, analyse comparative.

### Étape 03 — La Mémoire
**Objectif :** Implémenter une fenêtre glissante et un résumé automatique.
**Ce que vous apprenez :** Gestion du contexte, trade-off mémoire/coût.

### Étape 04 — La Persistance
**Objectif :** Sauvegarder les conversations dans SQLite ou JSON.
**Ce que vous apprenez :** Bases de données légères, gestion de sessions.

### Étape 05 — RAG (Retrieval-Augmented Generation)
**Objectif :** Ancrer le chatbot dans vos propres documents.
**Ce que vous apprenez :** ChromaDB, embeddings, chunking, évaluation RAG.

### Étape 06 — LangChain
**Objectif :** Utiliser le framework LangChain pour orchestrer le chatbot.
**Ce que vous apprenez :** Chaînes LangChain, mémoire intégrée, LCEL.

### Étape 07 — Docker
**Objectif :** Exposer le chatbot comme une API REST dockerisée.
**Ce que vous apprenez :** FastAPI, Docker, endpoints REST.

### Étape 08 — Monitoring
**Objectif :** Instrumenter l'API avec Prometheus et Grafana.
**Ce que vous apprenez :** Métriques custom, dashboards, observabilité.

### Étape 09 — Sécurité
**Objectif :** Sécuriser l'API avec JWT, rate limiting, sanitisation.
**Ce que vous apprenez :** Authentification, protection contre l'injection de prompt.

### Étape 10 — Tests de Charge (Locust)
**Objectif :** Tester la tenue en charge du chatbot.
**Ce que vous apprenez :** Tests de performance, Locust, analyse des résultats.

### Étape 11 — Tests Automatisés
**Objectif :** Couvrir l'application avec des tests unitaires, d'intégration et E2E.
**Ce que vous apprenez :** pytest, mocking, TestClient FastAPI, couverture de code.

### Étape 12 — Benchmark LLM-as-Judge
**Objectif :** Comparer plusieurs modèles sur un jeu d'évaluation standardisé.
**Ce que vous apprenez :** Évaluation automatique, LLM-as-Judge, analyse comparative.

---

## Conseils pédagogiques

1. **Ne sautez pas les étapes** — chaque étape introduit un concept qui sera réutilisé ensuite.
2. **Lisez le README de chaque étape** avant de lancer le code.
3. **Expérimentez** — modifiez les paramètres (MAX_HISTORY, modèles, etc.) pour comprendre l'impact.
4. **Comparez** — l'étape 12 vous permettra de voir concrètement les différences entre modèles.

---

## Structure des coûts indicatifs (OpenAI gpt-4o-mini)

| Étape | Appels estimés | Coût estimé |
|-------|---------------|-------------|
| 00 à 03 | ~50 | < 0,01 € |
| 04 à 06 | ~200 | < 0,05 € |
| 07 à 09 | ~500 | < 0,10 € |
| 10 à 12 | ~2000 | < 0,50 € |

*Tarifs indicatifs basés sur gpt-4o-mini à $0.15/1M tokens input, $0.60/1M tokens output.*

---

## Licence

Projet éducatif — libre d'utilisation et de modification.
