# 🧠 Évaluation — Étape 09 : Sécurité

> ⏱ Durée estimée : 60 min | Niveau : Avancé

## 🎯 Enjeu central

Un chatbot exposé sur internet est une cible. Cette étape empile **7 couches de protection** :
CORS, rate limiting, JWT, sanitization, prompt injection guard.
Le principe : **défense en profondeur** — aucune couche seule ne suffit,
chaque couche réduit la surface d'attaque.

```
Requête → CORS → Rate Limit → JWT → Sanitize → Prompt Guard → LLM
```

---

## ✅ Checklist de validation

- [ ] J'ai obtenu un token JWT via `POST /auth/token`
- [ ] J'ai vérifié qu'un appel sans token retourne un `401`
- [ ] J'ai exécuté `python test_security.py` → tous les tests verts
- [ ] J'ai testé manuellement une injection de prompt → `403`
- [ ] J'ai déclenché le rate limit (`429`) en envoyant trop de requêtes

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Décode la partie centrale (payload) de ton token JWT en Base64. Quelles informations y trouve-t-on ? À quelle heure expire-t-il ?

   > _________________________________________________________

2. Quelle requête exacte déclenche un `429` ? Après combien de secondes peux-tu de nouveau faire des requêtes ?

   > _________________________________________________________

3. Dans `test_security.py`, quels patterns d'injection ont été bloqués avec `403` ? Liste-en 3 et explique pourquoi ils sont dangereux.

   > _________________________________________________________

### Niveau 2 — Analyse
1. Le JWT est **stateless** : le serveur ne stocke pas le token. Comment vérifie-t-il qu'il est valide ? Quel serait l'impact si la `SECRET_KEY` était exposée dans le code ?

   > _________________________________________________________

2. Les 12 patterns regex de protection sont suffisants... jusqu'à ce qu'un attaquant trouve une formulation qui passe. Pourquoi la regex n'est-elle **pas** une défense suffisante contre l'injection de prompt ? Quelle approche complémentaire existe ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Tu sécurises un chatbot dans un hôpital (infirmiers + patients). Quelles couches de cette étape sont **obligatoires**, lesquelles sont **insuffisantes**, et quelles couches supplémentaires faudrait-il (HDS, RGPD données de santé) ?

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Dans `app/security.py`, ajoute un nouveau pattern d'injection dans `INJECTION_PATTERNS`
(une variante que les patterns actuels ne couvrent pas).
Relance l'API et vérifie dans `test_security.py` que ton pattern est bien bloqué.

**Pattern ajouté :** `_____________________________________________`

**Résultat du test :**
```
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Sécurité** : Comment la défense en profondeur (CORS + rate limit + JWT + injection guard) répond-elle aux exigences de sécurité d'un déploiement en production ? Quelles vulnérabilités OWASP Top 10 sont couvertes ?
- **RGPD** : Le JWT contient le `username` dans son payload. Si le token est intercepté, quelles données personnelles sont exposées ? Quelles mesures limitent ce risque (durée de vie, HTTPS, rotation des clés) ?

---

## 💡 Pour aller plus loin

- Utilise `jwt.io` pour décoder ton token : header, payload, signature.
- Cherche la différence entre `HS256` (HMAC) et `RS256` (RSA) pour les JWT.
- Lance `bandit -r app/` et analyse les résultats.
