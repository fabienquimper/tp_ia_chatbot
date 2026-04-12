# 🧠 Évaluation — Étape 07 : Docker & FastAPI

> ⏱ Durée estimée : 60 min | Niveau : Intermédiaire

## 🎯 Enjeu central

Un script Python sur ta machine n'est pas un service. Cette étape transforme le chatbot
en **API REST interrogeable par n'importe quel client** (web, mobile, autre service),
puis le containerise avec Docker pour garantir que "ça marche partout".
C'est le premier vrai déploiement du projet.

---

## ✅ Checklist de validation

- [ ] J'ai lancé l'API avec `uvicorn` et accédé à Swagger (`/docs`)
- [ ] J'ai testé `POST /chat` via Swagger avec une vraie question
- [ ] J'ai appelé `GET /history/{session_id}` et lu l'historique
- [ ] J'ai buildé l'image Docker et lancé le conteneur
- [ ] J'ai vérifié que `GET /health` répond depuis le conteneur

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Colle la réponse JSON complète de `GET /health`. Quels champs contient-elle ?

   > _________________________________________________________

2. Après 3 échanges, que retourne `GET /history/default` ? Quelle valeur a le champ `count` ?

   > _________________________________________________________

3. Quelle est la taille (en MB) de l'image Docker buildée (`docker images chatbot`) ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. FastAPI génère automatiquement la doc Swagger (`/docs`). Quel fichier Python définit le schéma des requêtes/réponses ? Pourquoi Pydantic est-il central dans cette approche ?

   > _________________________________________________________

2. Docker résout exactement quel problème ? Et quel problème ne résout-il **pas** ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Un client veut intégrer le chatbot dans son app mobile avec un SLA de P95 < 3s. Quels éléments de l'architecture actuelle représentent un risque ? Que proposes-tu ?

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Lance l'API et exécute `bash test_api.sh`. Observe les codes HTTP retournés.
Ensuite appelle `POST /chat` avec un `session_id` inventé, puis `GET /sessions`.
Ta session apparaît-elle ?

**Résultats de `test_api.sh` :**
```
_____________________________________________________________
```
**Sessions listées :**
```
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Architecture** : Comment l'exposition via API REST change le modèle de déploiement, d'intégration avec d'autres systèmes et de scalabilité par rapport à un script Python ?
- **Sécurité** : `GET /history/{session_id}` est accessible sans authentification. Quel risque ? Quelle mesure corrective (anticiper l'étape 09) ?

---

## 💡 Pour aller plus loin

- Ajoute un endpoint `DELETE /history/{session_id}` dans `app/main.py` et teste-le via Swagger.
- Inspecte le `Dockerfile` ligne par ligne : que fait chaque instruction (`FROM`, `WORKDIR`, `COPY`, `RUN`, `CMD`) ?
- Teste `docker-compose up --build` et compare avec `docker build + docker run`.
