# 🧠 Évaluation — Étape 01 : Le Chatbot Naïf (La Banane)

> ⏱ Durée estimée : 30 min | Niveau : Débutant

## 🎯 Enjeu central

Un LLM est **stateless** : il ne se souvient de rien entre deux appels. La "mémoire" du chatbot
est une illusion que tu crées en renvoyant tout l'historique à chaque requête.
Ça marche — mais ça ne survit pas au redémarrage, et ça grossit sans limite.

---

## ✅ Checklist de validation

- [ ] J'ai lancé `chatbot_naif.py` et eu une vraie conversation
- [ ] J'ai dit mon prénom, puis demandé "Quel est mon prénom ?" → réponse correcte
- [ ] J'ai quitté (`quit`) et relancé → vérifié que le bot ne se souvient plus
- [ ] J'ai observé comment la liste `msgs` grandit à chaque tour dans le code
- [ ] J'ai comparé `01_chatbot_naif_no_message_stack.py` et `02_chatbot_naif.py`

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Après 5 échanges, combien d'éléments contient `msgs` ? Décris le contenu du 3e élément.

   > _________________________________________________________

2. Que se passe-t-il exactement quand tu tapes `quit` et relances le script ? Quelle donnée est perdue ?

   > _________________________________________________________

3. Dans `01_chatbot_naif_no_message_stack.py` (sans historique), que répond le bot si tu lui donnes ton prénom puis demandes "Comment je m'appelle ?" à l'échange suivant ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. Pourquoi dit-on que la mémoire est une "illusion côté client" ? Qui fait vraiment le travail de mémorisation ?

   > _________________________________________________________

2. Si une conversation dure 200 échanges, combien de messages sont envoyés à l'API au 200e échange ? Quel impact sur le coût et la latence ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Tu déploies ce chatbot naïf pour 500 utilisateurs simultanés. Quels sont les 2 problèmes critiques du premier jour de prod ? Comment les hiérarchiser ?

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Modifie le `system prompt` pour donner au bot une personnalité différente
(ex : "Tu réponds uniquement en 10 mots maximum"). Lance une conversation et observe.

**Comportement observé :**
```
_____________________________________________________________
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Architecture** : Pourquoi l'architecture "stateless + historique côté client" est-elle à la fois une contrainte et un avantage pour un déploiement multi-utilisateurs ?
- **Risques** : Si l'historique n'est pas plafonné, quel risque technique et financier émerge après quelques jours d'utilisation intensive ? Proposez une métrique à surveiller.

---

## 💡 Pour aller plus loin

- Envoie la même question avec 0 et avec 10 échanges d'historique : compare la qualité des réponses.
- Mesure la taille de `msgs` après 20 échanges et estime son coût en tokens (~4 chars = 1 token).
- Lis la doc OpenAI sur le format `messages` : quels rôles existent au total ?
