# Étape 06 — LangChain

## Objectif
Refactoriser le code précédent avec LangChain. Swap Cloud/Local en 1 ligne.

## Ce qui change
| Avant (manuel) | Après (LangChain LCEL) |
|----------------|------------------------|
| `history[-MAX_HISTORY:]` | `K = 4` + `history[-K * 2:]` via LCEL |
| Construction manuelle de `msgs` | `ChatPromptTemplate` + `MessagesPlaceholder` |
| `client.chat.completions.create(...)` | `chain.invoke({"history": ..., "input": q})` |
| Config OpenAI/Local | `ChatOpenAI` / `ChatOllama` en 1 ligne |
| RAG manuel (retrieve + inject) | `retrieve()` + `chain.invoke()` en LCEL |

## Installation
```bash
pip install -r requirements.txt
cp .env.example .env
```

## Scripts

### chatbot_langchain.py — Chatbot simple
```bash
python chatbot_langchain.py
```

### chatbot_langchain_rag.py — Chatbot RAG
```bash
# Nécessite que l'étape 05 soit indexée :
# cd ../etape_05_rag && python indexer.py

python chatbot_langchain_rag.py
```

## Switcher Cloud ↔ Local
```python
# Cloud (1 ligne)
llm = ChatOpenAI(model="gpt-4o-mini")

# Local LM Studio (1 ligne)
llm = ChatOpenAI(model="mistral-7b", base_url="http://localhost:1234/v1", api_key="lm-studio")

# Local Ollama (1 ligne)
from langchain_community.chat_models import ChatOllama
llm = ChatOllama(model="mistral")
```

## Exercice
1. Portez votre code étape 03 vers LangChain
2. Changez `ChatOpenAI` → `ChatOllama` (si Ollama installé)
3. Comparez le nombre de lignes : avant vs après
