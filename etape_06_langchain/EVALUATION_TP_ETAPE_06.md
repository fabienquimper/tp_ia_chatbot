# 🧠 Évaluation — Étape 06 : LangChain

> ⏱ Durée estimée : 45 min | Niveau : Intermédiaire

## 🎯 Enjeu central

LangChain est un framework d'orchestration LLM. Sa vraie valeur : faire la **même chose avec
moins de code** et permettre le **swap de backend en une ligne**.
Cette étape pose la question fondamentale de l'abstraction : quand est-elle utile, quand est-elle
une complexité inutile ?

---

## ✅ Checklist de validation

- [ ] J'ai lancé `chatbot_langchain.py` et eu une conversation fonctionnelle
- [ ] J'ai comparé le nombre de lignes avec le chatbot de l'étape 03
- [ ] J'ai lu la section "Switcher Cloud ↔ Local" du README et compris le changement
- [ ] J'ai lancé `chatbot_langchain_rag.py` (après indexation étape 05)

---

## 🔍 Questions de compréhension

### Niveau 1 — Observation
1. Combien de lignes compte `chatbot_langchain.py` vs `memory_window.py` (étape 03) ? Quelle classe LangChain remplace la gestion manuelle de `msgs` ?

   > _________________________________________________________

2. Quel paramètre `k` est configuré dans `ConversationBufferWindowMemory` ? À quoi correspond-il par rapport à `MAX_HISTORY` ?

   > _________________________________________________________

3. Dans `chatbot_langchain_rag.py`, quelle classe LangChain orchestre la recherche ChromaDB + la génération LLM en une seule ligne ?

   > _________________________________________________________

### Niveau 2 — Analyse
1. LangChain abstrait le LLM derrière une interface commune. Quel est le **risque** de cette abstraction en production ? (Pense aux mises à jour de LangChain, aux breaking changes, aux performances.)

   > _________________________________________________________

2. `ConversationalRetrievalChain` enchaîne deux appels LLM. Pourquoi deux ? Que fait chacun ? Quel impact sur la latence et le coût ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Un client te demande de choisir entre code LLM "à la main" vs LangChain. Quels facteurs pèsent dans chaque sens ? Donne une recommandation contextuelle (startup vs grand compte, prototype vs prod).

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Dans `chatbot_langchain.py`, change `k=4` en `k=1` dans `ConversationBufferWindowMemory`.
Conduis 5 échanges et observe la cohérence. Remets `k=8` et compare.

**Comportement avec k=1 :**
```
_____________________________________________________________
```

---

## 📋 Lien avec le dossier E8

- **Architecture** : Comment LangChain facilite la portabilité entre fournisseurs LLM (OpenAI, Anthropic, Ollama) ? Quel risque de "vendor lock-in" reste présent malgré l'abstraction ?
- **Risques** : LangChain est open-source avec des mises à jour fréquentes. Comment gérez-vous ce risque en production (versioning, tests de non-régression) ?

---

## 💡 Pour aller plus loin

- Explore LCEL (LangChain Expression Language) : quelle est la syntaxe avec les pipes `|` ?
- Si Ollama est installé, remplace `ChatOpenAI` par `ChatOllama` et mesure la différence de latence.
- Cherche la notion de "chain" vs "agent" dans LangChain : quelle est la différence fondamentale ?
