# Étape 05 — RAG (Retrieval-Augmented Generation)

## Objectif
Connecter le chatbot à une base de connaissances documentaire.

## Architecture RAG

```
Question utilisateur
       ↓
[ChromaDB] → Recherche sémantique → 3 chunks pertinents
       ↓
Injection dans le system prompt
       ↓
[LLM] → Réponse basée sur les docs
```

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
```

## Étapes

### 1. Indexer les documents
```bash
python indexer.py
```
Indexe tous les fichiers `.txt` du dossier `data/`.

### 2. Lancer le chatbot RAG
```bash
python rag_chromadb.py
```

### 3. Évaluer la qualité
```bash
python evaluer_rag.py
```
Objectif : Hit Rate > 80%

## Questions de test
- "Quel est le prix de CloudSync Pro ?"
- "Comment contacter le support ?"
- "Quelles sont les limites de l'API ?"
- "Où sont vos bureaux ?"

## KPI : Hit Rate
```
Hit Rate = questions correctement répondues / total questions
```
Objectif production : > 80%
