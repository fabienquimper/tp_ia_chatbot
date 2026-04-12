# 🧠 Évaluation — Étape 11 : Tests Automatisés (pytest)

> ⏱ Durée estimée : 60 min | Niveau : Avancé

## 🎯 Enjeu central

Un test qui appelle l'API OpenAI coûte $0.001 et prend 2s.
Avec 100 tests lancés 50 fois par jour → **$5/jour** juste pour les tests.
Cette étape introduit les 3 niveaux de tests et la pratique fondamentale du **mock** :
remplacer le LLM par une réponse instantanée et déterministe.

```
test_unit        → fonction seule          (pas de FastAPI, pas de LLM)
test_integration → FastAPI en mémoire      (LLM mocké, DB temporaire)
test_e2e         → vrai serveur HTTP       (vrai LLM, vraie DB)
```

---

## ✅ Checklist de validation

- [ ] J'ai lancé `pytest` et obtenu 100% de tests verts
- [ ] J'ai lancé `pytest --cov=app` et vérifié couverture ≥ 70%
- [ ] J'ai lancé `pytest tests/test_unit.py -v` et compris chaque test
- [ ] J'ai lancé `pytest tests/test_integration.py -v` et vérifié que le LLM est mocké
- [ ] J'ai tenté les tests E2E (API lancée en arrière-plan)

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Quel est le taux de couverture global après `pytest --cov=app` ? Quel module a la couverture la plus basse ?

   > Coverage global : ___% | Module le plus faible : ___________

2. Dans `conftest.py`, que fait exactement la fixture `mock_llm` ? Quelle valeur retourne-t-elle à la place d'un vrai appel ?

   > _________________________________________________________

3. Combien de temps prend la suite complète (`pytest`) ? Estime le temps sans mock (vrais appels LLM).

   > Avec mock : ___s | Sans mock (estimation) : ___s

### Niveau 2 — Analyse
1. Les tests d'intégration utilisent `TestClient` de FastAPI. Qu'est-ce que `TestClient` simule et qu'est-ce qu'il ne simule **pas** ?

   > _________________________________________________________

2. Un test E2E passe en CI mais échoue en production. Cite 3 raisons possibles — et comment les tests d'intégration avec mocks évitent (ou pas) ce problème.

   > _________________________________________________________

### Niveau 3 — Décision
1. Un développeur propose de supprimer les tests unitaires et ne garder que les E2E "qui testent vraiment ce que l'utilisateur voit". Pour ou contre ? Argumente avec les concepts de coût, vitesse et déterminisme.

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Dans `tests/test_unit.py`, ajoute un test qui vérifie qu'un message contenant `<script>`
est bien sanitisé par `sanitize_message()`. Lance-le avec `pytest tests/test_unit.py -v -k "xss"`.

**Test ajouté :**
```python
def test_xss_sanitization():
    # ton code ici
    pass
```

**Résultat :** `_____________________________________________`

---

## 📋 Lien avec le dossier E8

- **Tests** : Comment organiseriez-vous la stratégie de tests (unit / intégration / E2E) dans un pipeline CI/CD ? Quels tests bloquent le merge, lesquels sont facultatifs ?
- **Qualité** : La couverture à 70% est-elle suffisante ? Quelles parties du code seraient les plus risquées à laisser sans tests (logique de sécurité, gestion des erreurs LLM) ?

---

## 💡 Pour aller plus loin

- Génère le rapport HTML : `pytest --cov=app --cov-report=html` et identifie les lignes non couvertes.
- Essaie `pytest -x` (stop au 1er échec) : dans quel contexte est-ce utile ?
- Cherche la différence entre **mock**, **stub** et **fake**.
