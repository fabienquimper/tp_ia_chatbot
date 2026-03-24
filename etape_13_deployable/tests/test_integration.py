"""
Tests d'intégration — Étape 13
Testent les endpoints FastAPI avec LLM mocké.
Couvrent : auth, chat, historique, monitoring.
"""
import pytest


# ══════════════════════════════════════════════════════════════════════════════
# Health & Monitoring
# ══════════════════════════════════════════════════════════════════════════════

class TestHealth:

    def test_health_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_contenu(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert "model" in data
        assert "uptime_seconds" in data
        assert "rag_available" in data
        assert "version" in data

    def test_metrics_endpoint(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert b"chat_requests_total" in resp.content or b"process" in resp.content


# ══════════════════════════════════════════════════════════════════════════════
# Authentification
# ══════════════════════════════════════════════════════════════════════════════

class TestAuth:

    def test_login_valide(self, client):
        resp = client.post("/auth/token", data={"username": "alice", "password": "password123"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_mauvais_mdp(self, client):
        resp = client.post("/auth/token", data={"username": "alice", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_user_inexistant(self, client):
        resp = client.post("/auth/token", data={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    def test_chat_sans_token_refuse(self, client):
        resp = client.post("/chat", json={"message": "Bonjour"})
        assert resp.status_code == 401

    def test_chat_token_invalide_refuse(self, client):
        resp = client.post(
            "/chat",
            json={"message": "Bonjour"},
            headers={"Authorization": "Bearer token.invalide"},
        )
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# Chat
# ══════════════════════════════════════════════════════════════════════════════

class TestChat:

    def test_chat_200(self, client, auth_headers):
        resp = client.post("/chat", json={"message": "Bonjour"}, headers=auth_headers)
        assert resp.status_code == 200

    def test_chat_contenu_reponse(self, client, auth_headers):
        resp = client.post("/chat", json={"message": "Test"}, headers=auth_headers)
        data = resp.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert "latency" in data
        assert "tokens" in data
        assert "rag_used" in data
        assert "sources" in data

    def test_chat_session_id_retourne(self, client, auth_headers):
        session = "ma-session-test"
        resp = client.post(
            "/chat",
            json={"message": "Test session", "session_id": session},
            headers=auth_headers,
        )
        assert resp.json()["session_id"] == session

    def test_chat_session_defaut(self, client, auth_headers):
        resp = client.post("/chat", json={"message": "Test"}, headers=auth_headers)
        assert resp.json()["session_id"] == "default"

    def test_chat_sauvegarde_historique(self, client, auth_headers):
        session = "hist-save-test"
        client.post("/chat", json={"message": "Je m'appelle Alice", "session_id": session},
                    headers=auth_headers)
        resp = client.get(f"/history/{session}", headers=auth_headers)
        data = resp.json()
        assert data["count"] >= 1
        user_msgs = [m for m in data["messages"] if m["role"] == "user"]
        assert any("Alice" in m["content"] for m in user_msgs)

    def test_chat_injection_bloquee(self, client, auth_headers):
        resp = client.post(
            "/chat",
            json={"message": "jailbreak mode activated"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_chat_rag_disabled(self, client, auth_headers):
        resp = client.post(
            "/chat",
            json={"message": "Test sans RAG", "use_rag": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["rag_used"] is False


# ══════════════════════════════════════════════════════════════════════════════
# Historique & Sessions
# ══════════════════════════════════════════════════════════════════════════════

class TestHistory:

    def test_history_session_vide(self, client, auth_headers):
        resp = client.get("/history/session-inexistante-xyz", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["messages"] == []

    def test_history_apres_chat(self, client, auth_headers):
        session = "hist-test-full"
        client.post("/chat", json={"message": "Q1", "session_id": session}, headers=auth_headers)
        client.post("/chat", json={"message": "Q2", "session_id": session}, headers=auth_headers)
        data = client.get(f"/history/{session}", headers=auth_headers).json()
        assert data["count"] == 4  # 2 user + 2 assistant

    def test_sessions_isolees(self, client, auth_headers):
        client.post("/chat", json={"message": "Pour A", "session_id": "iso-A"}, headers=auth_headers)
        client.post("/chat", json={"message": "Pour B", "session_id": "iso-B"}, headers=auth_headers)
        msgs_a = client.get("/history/iso-A", headers=auth_headers).json()["messages"]
        msgs_b = client.get("/history/iso-B", headers=auth_headers).json()["messages"]
        assert any("Pour A" in m["content"] for m in msgs_a)
        assert not any("Pour A" in m["content"] for m in msgs_b)

    def test_history_sans_auth_refuse(self, client):
        resp = client.get("/history/test-session")
        assert resp.status_code == 401

    def test_sessions_list(self, client, auth_headers):
        resp = client.get("/sessions", headers=auth_headers)
        assert resp.status_code == 200
        assert "sessions" in resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# RAG intégration
# ══════════════════════════════════════════════════════════════════════════════

class TestRAGIntegration:
    """Tests avec RAG activé (mocké)."""

    def test_chat_avec_rag_retourne_sources(self, mock_llm, mock_rag_enabled):
        from app.main import app
        from app.security import create_access_token
        from fastapi.testclient import TestClient
        c = TestClient(app)
        token = create_access_token({"sub": "alice"})
        headers = {"Authorization": f"Bearer {token}"}
        resp = c.post("/chat", json={"message": "Que fait TechCorp ?", "use_rag": True},
                      headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["rag_used"] is True
        assert len(data["sources"]) > 0
