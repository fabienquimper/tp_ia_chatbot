# 🧠 Évaluation — Étape 05 : RAG (Retrieval-Augmented Generation)

> ⏱ Durée estimée : 60 min | Niveau : Intermédiaire

## 🎯 Enjeu central

Un LLM ne sait que ce qu'il a vu pendant son entraînement. Pour répondre sur tes propres
documents, il faut lui **injecter le contexte pertinent à chaque requête**.
C'est le RAG : chercher dans une base vectorielle, puis envoyer les passages au LLM.
KPI central : le Hit Rate — combien de questions trouvent une réponse correcte dans tes docs ?

---

## ✅ Checklist de validation

- [ ] J'ai lancé `indexer.py` et indexé les documents du dossier `data/`
- [ ] J'ai lancé `rag_chromadb.py` et posé des questions couvertes par les docs
- [ ] J'ai posé une question hors-sujet et observé la réponse
- [ ] J'ai lancé `evaluer_rag.py` et noté mon Hit Rate
- [ ] J'ai inspecté le dossier `chroma_db/` créé par l'indexation

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Quel Hit Rate as-tu obtenu avec `evaluer_rag.py` ? Quelles questions ont échoué et pourquoi selon toi ?

   > _________________________________________________________

2. Quand tu poses "Quel est le prix de CloudSync Pro ?", combien de chunks ChromaDB renvoie-t-il ? Quelle est leur longueur approximative ?

   > _________________________________________________________

3. Que répond le bot si tu poses une question sur un sujet absent des documents (ex : "Quelle est la météo aujourd'hui ?") ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. Le pipeline RAG est `embed → store → retrieve → inject → generate`. À quelle étape intervient le LLM ? À quelle étape intervient ChromaDB ? Pourquoi les séparer ?

   > _________________________________________________________

2. Si tu indexes un doc de 100 pages en chunks de 500 tokens, combien de chunks obtiens-tu ? Quel est l'impact sur la pertinence si les chunks sont trop petits ? Trop grands ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Tu déploies un RAG sur une base de 50 000 pages. Quels sont les 3 risques principaux (qualité, coût, latence) et comment les anticipes-tu dans la conception ?

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Ajoute un fichier `.txt` dans `data/` avec 5-10 phrases inventées sur un sujet fictif.
Relance `indexer.py` puis pose une question sur ce nouveau contenu. Le RAG le retrouve-t-il ?

**Question posée :** `__________________________________________________`

**Réponse du bot :**
```
_____________________________________________________________
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Architecture** : Décrivez l'architecture RAG implémentée : rôle de ChromaDB, rôle des embeddings, et pourquoi ce choix est préférable à un fine-tuning pour une base documentaire d'entreprise.
- **RGPD** : Si les documents indexés contiennent des données personnelles, quelles obligations RGPD s'appliquent à la base vectorielle ? Comment implémenter le droit à l'effacement dans un système RAG ?

---

## 💡 Pour aller plus loin

- Modifie la taille des chunks (200, 500, 1000 tokens) et mesure l'impact sur le Hit Rate.
- Inspecte le dossier `chroma_db/` : dans quel format les embeddings sont-ils stockés ?
- Cherche la différence entre **sparse retrieval** (BM25) et **dense retrieval** (embeddings).
