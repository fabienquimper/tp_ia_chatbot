# ── Stage 1 : Builder ─────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2 : Test Runner ─────────────────────────────────────────────────
# Utilisé uniquement dans la CI (target: test)
FROM builder AS test

WORKDIR /app

# Expose les packages installés avec --prefix=/install par le stage builder
ENV PATH=/install/bin:$PATH
ENV PYTHONPATH=/install/lib/python3.11/site-packages:/app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements-dev.txt

COPY . .
ENV DB_PATH=/tmp/test_chat.db

# Lance les tests (exit 1 si échec → build bloqué)
RUN python -m pytest tests/ -v --tb=short --cov=app \
    --cov-report=term-missing --cov-fail-under=70 \
    -p no:warnings


# ── Stage 3 : Production ──────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Utilisateur non-root pour la sécurité
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot

WORKDIR /app

# ── Layers stables (cachés sauf si requirements.txt change) ───────────────

# Dépendances Python compilées
COPY --from=builder /install /usr/local

# Dépendances système runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dossier données — créé ICI avant le code (ne sera pas re-exécuté)
RUN mkdir -p /app/data/chroma_db && chown -R chatbot:chatbot /app/data

# ── Documents RAG (layer stable — change moins souvent que le code) ────────
COPY --chown=chatbot:chatbot data/docs/ ./docs/

# ── Layer volatile (invalidé à chaque changement de code) ─────────────────

# --chown intégré : évite un RUN chown séparé après le COPY
COPY --chown=chatbot:chatbot app/ ./app/
COPY --chown=chatbot:chatbot scripts/ ./scripts/

# HOME → /app/data (volume writable) pour que ChromaDB puisse y écrire
# son cache de modèle ONNX (évite PermissionError sur /home/chatbot inexistant)
ENV HOME=/app/data

USER chatbot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Workers = 1 par défaut (scale via K8S/replicas)
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
