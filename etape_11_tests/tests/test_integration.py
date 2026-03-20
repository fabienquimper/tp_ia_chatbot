"""
Tests d'intégration — Testent l'API avec LLM mocké.
Vérifient le comportement complet des endpoints.
"""
import pytest


class TestHealth:
    """Tests de l'endpoint /health."""

    def test_health_retourne_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_contient_status_ok(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_contient_model(self, client):
        response = client.get("/health")
        data = response.json()
        assert "model" in data
        assert len(data["model"]) > 0

    def test_health_contient_uptime(self, client):
        response = client.get("/health")
        data = response.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


class TestChat:
    """Tests de l'endpoint /chat."""

    def test_chat_retourne_200(self, client):
        response = client.post(
            "/chat",
            json={"message": "Bonjour !", "session_id": "test-001"}
        )
        assert response.status_code == 200

    def test_chat_contient_reply(self, client):
        response = client.post(
            "/chat",
            json={"message": "Comment tu t'appelles ?", "session_id": "test-002"}
        )
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0

    def test_chat_contient_session_id(self, client):
        session = "ma-session-unique"
        response = client.post(
            "/chat",
            json={"message": "Test", "session_id": session}
        )
        data = response.json()
        assert data["session_id"] == session

    def test_chat_contient_latency(self, client):
        response = client.post(
            "/chat",
            json={"message": "Test latence", "session_id": "test-lat"}
        )
        data = response.json()
        assert "latency" in data
        assert data["latency"] >= 0

    def test_chat_contient_tokens(self, client):
        response = client.post(
            "/chat",
            json={"message": "Test tokens", "session_id": "test-tok"}
        )
        data = response.json()
        assert "tokens" in data
        assert data["tokens"] > 0

    def test_chat_sauvegarde_dans_historique(self, client):
        session = "test-history-save"
        client.post("/chat", json={"message": "Je m'appelle Alice", "session_id": session})

        response = client.get(f"/history/{session}")
        data = response.json()
        assert data["count"] >= 1
        messages = data["messages"]
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert any("Alice" in m["content"] for m in user_msgs)

    def test_chat_message_vide_refuse(self, client):
        response = client.post(
            "/chat",
            json={"message": "", "session_id": "test"}
        )
        assert response.status_code == 422  # Validation Pydantic

    def test_chat_session_defaut(self, client):
        response = client.post(
            "/chat",
            json={"message": "Test sans session"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "default"


class TestHistory:
    """Tests de l'endpoint /history."""

    def test_history_session_vide(self, client):
        response = client.get("/history/session-inexistante-xyz-123")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["messages"] == []

    def test_history_apres_chat(self, client):
        session = "test-hist-after-chat"
        client.post("/chat", json={"message": "Bonjour", "session_id": session})
        client.post("/chat", json={"message": "Comment ça va ?", "session_id": session})

        response = client.get(f"/history/{session}")
        data = response.json()
        assert data["count"] == 4  # 2 user + 2 assistant

    def test_history_contient_roles(self, client):
        session = "test-roles"
        client.post("/chat", json={"message": "Test", "session_id": session})

        response = client.get(f"/history/{session}")
        messages = response.json()["messages"]
        roles = {m["role"] for m in messages}
        assert "user" in roles
        assert "assistant" in roles

    def test_history_sessions_isolees(self, client):
        client.post("/chat", json={"message": "Pour session A", "session_id": "session-A"})
        client.post("/chat", json={"message": "Pour session B", "session_id": "session-B"})

        hist_a = client.get("/history/session-A").json()["messages"]
        hist_b = client.get("/history/session-B").json()["messages"]

        contents_a = [m["content"] for m in hist_a]
        contents_b = [m["content"] for m in hist_b]

        assert any("session A" in c for c in contents_a)
        assert not any("session A" in c for c in contents_b)


class TestLLMMock:
    """Vérifie que le LLM est bien mocké dans les tests."""

    def test_llm_est_mocke(self, client, mock_llm):
        response = client.post(
            "/chat",
            json={"message": "Test mock", "session_id": "mock-test"}
        )
        assert response.status_code == 200
        data = response.json()
        # La réponse doit venir du mock
        assert data["reply"] == "Réponse de test du LLM mocké."
        # Le mock doit avoir été appelé une fois
        assert mock_llm.call_count == 1
