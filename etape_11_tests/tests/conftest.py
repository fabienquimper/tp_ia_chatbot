"""
Fixtures pytest pour tous les tests.
"""
import os, pytest, tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def use_temp_db(tmp_path):
    """Utilise une base de données temporaire pour chaque test."""
    db_path = str(tmp_path / "test_chat.db")
    with patch.dict(os.environ, {"DB_PATH": db_path}):
        # Réinitialise la DB pour ce test
        from app import database
        database.init_db()
        yield db_path

@pytest.fixture
def mock_llm():
    """Mock du LLM pour éviter les vrais appels API."""
    with patch("app.llm.get_reply") as mock:
        mock.return_value = ("Réponse de test du LLM mocké.", 15)
        yield mock

@pytest.fixture
def client(mock_llm):
    """Client de test FastAPI avec LLM mocké."""
    from app.main import app
    # Réinitialiser le module pour avoir la bonne DB
    from app.database import init_db
    init_db()
    return TestClient(app)

@pytest.fixture
def client_no_mock():
    """Client de test sans mock (pour tests d'intégration réels — nécessite clé API)."""
    from app.main import app
    from app.database import init_db
    init_db()
    return TestClient(app)
