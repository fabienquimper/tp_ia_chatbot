"""
Tests E2E — Testent contre une API réellement lancée.
Ces tests sont ignorés si l'API n'est pas disponible.
"""
import pytest
import httpx

BASE_URL = "http://localhost:8000"

def api_available() -> bool:
    """Vérifie si l'API est disponible."""
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

skip_if_no_api = pytest.mark.skipif(
    not api_available(),
    reason="API non disponible sur localhost:8000. Lancez d'abord uvicorn app.main:app"
)


@skip_if_no_api
class TestE2EHealth:
    def test_health_check(self):
        r = httpx.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@skip_if_no_api
class TestE2EChat:
    def test_chat_round_trip(self):
        r = httpx.post(
            f"{BASE_URL}/chat",
            json={"message": "Bonjour !", "session_id": "e2e-test"},
            timeout=30
        )
        assert r.status_code == 200
        data = r.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    def test_history_persistence(self):
        session = "e2e-history-test"
        httpx.post(f"{BASE_URL}/chat", json={"message": "Je suis un test E2E", "session_id": session}, timeout=30)
        r = httpx.get(f"{BASE_URL}/history/{session}")
        assert r.status_code == 200
        assert r.json()["count"] > 0
