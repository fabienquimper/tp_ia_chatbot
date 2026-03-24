"""
Fixtures pytest pour l'étape 13.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def disable_rate_limit():
    """
    Réinitialise le stockage du rate limiter avant chaque test.
    Le limiter est un singleton module-level : les compteurs s'accumulent
    entre les tests (notamment les 3 appels directs de TestAuth à /auth/token).
    """
    from app.security import limiter
    limiter._enabled = False
    try:
        if hasattr(limiter, "_storage"):
            limiter._storage.reset()
    except Exception:
        pass
    yield
    limiter._enabled = True


@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    """Base de données temporaire isolée pour chaque test."""
    db_path = str(tmp_path / "test_chat.db")
    with patch.dict(os.environ, {"DB_PATH": db_path}):
        from app import database
        database.DB_PATH = db_path
        database.init_db()
        yield db_path
    # Réinitialise le module pour le prochain test
    from importlib import reload
    import app.database
    app.database.DB_PATH = os.environ.get("DB_PATH", "/app/data/chat.db")


@pytest.fixture
def mock_llm():
    """Mock du LLM — évite les vrais appels API."""
    with patch("app.main.get_reply") as mock:
        mock.return_value = ("Réponse de test du LLM mocké.", 15)
        yield mock


@pytest.fixture
def mock_rag_disabled():
    """Désactive le RAG pour les tests."""
    with patch("app.main.rag_module.is_available", return_value=False), \
         patch("app.main.rag_module.init_rag", return_value=False):
        yield


@pytest.fixture
def mock_rag_enabled():
    """RAG activé avec des documents factices."""
    sample_docs = [
        {"content": "TechCorp offre des solutions d'IA avancées.", "source": "techcorp.txt"},
        {"content": "Notre support est disponible 24/7.", "source": "faq.txt"},
    ]
    with patch("app.main.rag_module.is_available", return_value=True), \
         patch("app.main.rag_module.retrieve", return_value=sample_docs), \
         patch("app.main.rag_module.build_context", return_value="TechCorp context."):
        yield sample_docs


@pytest.fixture
def client(mock_llm, mock_rag_disabled):
    """Client de test — LLM mocké, RAG désactivé."""
    from app.main import app
    from app.database import init_db
    init_db()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """En-têtes d'authentification JWT valides.
    Crée le token directement (sans passer par /auth/token) pour ne pas
    consommer le rate limit partagé entre tous les tests de la session.
    """
    from app.security import create_access_token
    token = create_access_token({"sub": "alice"})
    return {"Authorization": f"Bearer {token}"}
