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
1. Combien de lignes compte `chatbot_langchain.py` vs `01_memory_window.py` (étape 03) ? Quelle structure LangChain (prompt + chain LCEL) remplace la construction manuelle de `msgs` ?

   > _________________________________________________________

2. Dans `chatbot_langchain.py`, la variable `K = 4` contrôle la fenêtre glissante. À quoi correspond-elle par rapport à `MAX_HISTORY` de l'étape 03 ? Retrouve la ligne où `history` est tronquée.

   > _________________________________________________________

3. Dans `chatbot_langchain_rag.py`, quelle syntaxe LCEL orchestre la recherche ChromaDB + la génération LLM ? (Cherche la ligne avec `chain = prompt | llm | ...`)

   > _________________________________________________________

### Niveau 2 — Analyse
1. LangChain abstrait le LLM derrière une interface commune. Quel est le **risque** de cette abstraction en production ? (Pense aux mises à jour de LangChain, aux breaking changes, aux performances.)

   > _________________________________________________________

2. Dans `chatbot_langchain_rag.py`, on fait d'abord un `retrieve(q)` puis un `chain.invoke(...)`. Ce sont deux opérations distinctes. Quel est l'avantage de les séparer (vs une chaîne tout-en-un comme `ConversationalRetrievalChain`) ? Quel impact sur la lisibilité et le débogage ?

   > _________________________________________________________

### Niveau 3 — Décision
1. Un client te demande de choisir entre code LLM "à la main" vs LangChain. Quels facteurs pèsent dans chaque sens ? Donne une recommandation contextuelle (startup vs grand compte, prototype vs prod).

   > _________________________________________________________
   > _________________________________________________________

---

## 🧪 Mini-expérience guidée

Dans `chatbot_langchain.py`, trouve la ligne `K = 4` et change-la en `K = 1`.
Conduis 5 échanges et observe la cohérence. Remets `K = 4` et compare.

**Comportement avec K=1 :**
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
