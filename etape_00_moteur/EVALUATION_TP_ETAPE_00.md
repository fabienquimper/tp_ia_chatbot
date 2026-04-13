# 🧠 Évaluation — Étape 00 : Le Moteur

> ⏱ Durée estimée : 30 min | Niveau : Débutant

## 🎯 Enjeu central

Avant d'écrire une seule ligne de logique, il faut que la connexion au LLM fonctionne.
Cette étape pose la fondation : un LLM cloud ou local expose **la même interface REST**,
les clés API ne doivent **jamais** être dans le code, et la latence de départ est déjà mesurable.

---

## ✅ Checklist de validation

- [ ]  J'ai créé mon `.env` à partir de `.env.example` et ajouté ma clé API
- [ ]  J'ai lancé `python demo_connexion.py` et obtenu une réponse du LLM (LM Studio en local)
- [ ]  J'ai lancé `python demo_connexion.py` et obtenu une réponse du LLM (LM Studio sur un serveur local)
- [ ]  J'ai noté la latence affichée (mode local LM Studio)
- [ ]  J'ai vérifié que le fichier `.env` **n'apparaît pas** dans `git status`

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation

1. Quelle latence as-tu obtenue lors de ton premier appel (`demo_connexion.py`) ? En combien de millisecondes ?
2. Qu'affiche `python config.py` sur ton poste ? Quel mode est actif (cloud / local) et quel modèle est configuré ?
3. Si tu ouvres ton `.env`, quelles variables y sont définies ? Laquelle serait catastrophique à exposer sur GitHub ?

### Niveau 2 — Analyse

1. Pourquoi utilise-t-on `python-dotenv` plutôt que d'écrire `api_key = "sk-..."` directement dans le code ? Que se passerait-il avec un `git push` avec la clé en dur ?
2. Cloud et local utilisent la **même interface** (`client.chat.completions.create`). Qu'est-ce que ça implique pour le code des étapes suivantes ?

### Niveau 3 — Décision

1. Tu dois choisir entre cloud (OpenAI) et local (LM Studio) pour un chatbot interne à une banque. Quels critères guident ta décision ? Cite au moins 3 dimensions (coût, conformité, latence, confidentialité...).

---

## 🧪 Mini-expérience guidée

Dans `demo_connexion.py`, change `max_tokens` à `5`. Que se passe-t-il ? La réponse est-elle complète ?

**Observation :**

```
_____________________________________________________________
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Architecture** : Décris en 3-5 phrases comment la gestion des clés API via variables d'environnement s'inscrit dans les bonnes pratiques de sécurité (secrets managers, AWS Secrets Manager, HashiCorp Vault).
- **Réglementaire** : Si le chatbot utilise l'API OpenAI, les messages transitent par des serveurs américains. Quelles implications pour le RGPD et la souveraineté des données ?

---

## 💡 Pour aller plus loin

- Teste LM Studio : compare la latence cloud vs local.
- Calcule le coût de 10 000 messages de 500 tokens avec `gpt-4o-mini` (page pricing OpenAI).
- Explore la différence entre `max_tokens` et `temperature`.
