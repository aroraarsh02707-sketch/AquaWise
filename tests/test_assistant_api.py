"""
Tests for AquaWise Assistant REST API (Task 6).

Endpoints tested:
- POST /api/assistant/chat
- GET /api/assistant/conversations
- GET /api/assistant/conversations/<id>

Validates:
- Authentication required
- Successful chat (mocking AI)
- Offline/fallback chat
- Conversation creation and reuse
- Conversation history
- Ownership protection
- Context injection
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app import create_app, seed_achievements
from backend.models import (
    db, User, Assessment, ConsumptionBreakdown, AIConversation, AIMessage
)


@pytest.fixture
def app():
    """Create test application with in-memory database."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        seed_achievements()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user_a(app):
    user = User(name="User A", email="usera@test.com", user_type="household")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def user_b(app):
    user = User(name="User B", email="userb@test.com", user_type="household")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def user_a_context(user_a):
    assessment = Assessment(
        user_id=user_a.id,
        assessment_type="household",
        daily_consumption=450.0,
        weekly_consumption=3150.0,
        monthly_consumption=13500.0,
        water_saver_score=60,
    )
    db.session.add(assessment)
    db.session.flush()

    b1 = ConsumptionBreakdown(
        assessment_id=assessment.id,
        category="Bathing",
        litres_per_day=270.0,
        percentage=60.0
    )
    db.session.add(b1)
    db.session.commit()
    return assessment

@pytest.fixture
def user_a_conversation(user_a):
    conv = AIConversation(user_id=user_a.id, title="Test Chat")
    db.session.add(conv)
    db.session.flush()
    m1 = AIMessage(conversation_id=conv.id, role="user", message="Hello")
    m2 = AIMessage(conversation_id=conv.id, role="assistant", message="Hi!")
    db.session.add_all([m1, m2])
    db.session.commit()
    return conv


def login(client, email, password="Password123!"):
    return client.post("/api/auth/login", json={"email": email, "password": password})

class TestAssistantAPI:

    def test_unauthenticated_requests(self, client):
        res = client.post("/api/assistant/chat", json={"message": "hello"})
        assert res.status_code == 401
        
        res = client.get("/api/assistant/conversations")
        assert res.status_code == 401

        res = client.get("/api/assistant/conversations/1")
        assert res.status_code == 401

    def test_chat_missing_message(self, client, user_a):
        login(client, user_a.email)
        res = client.post("/api/assistant/chat", json={})
        assert res.status_code == 400
        assert res.get_json()["success"] is False

    @patch("backend.services.ai_service.requests.post")
    def test_chat_creates_new_conversation(self, mock_post, client, user_a, monkeypatch):
        login(client, user_a.email)
        monkeypatch.setenv("AI_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "AI Response"}]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        res = client.post("/api/assistant/chat", json={"message": "First message"})
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        
        payload = data["data"]
        assert "conversation_id" in payload
        assert payload["message"] == "AI Response"
        assert payload["source"] == "ai"

        # Check DB
        conv = db.session.get(AIConversation, payload["conversation_id"])
        assert conv is not None
        assert conv.user_id == user_a.id
        assert conv.title.startswith("First message")
        assert len(conv.messages) == 2

    def test_chat_offline_fallback(self, client, user_a, monkeypatch):
        login(client, user_a.email)
        # Ensure offline mode
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")

        res = client.post("/api/assistant/chat", json={"message": "how to save water in toilet?"})
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["source"] == "fallback"
        assert "Dual-Flush" in data["data"]["message"]

    @patch("backend.services.ai_service.requests.post")
    def test_chat_reuses_conversation(self, mock_post, client, user_a, user_a_conversation, monkeypatch):
        login(client, user_a.email)
        monkeypatch.setenv("AI_API_KEY", "test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Follow up response"}]}}]
        }
        mock_post.return_value = mock_response

        res = client.post("/api/assistant/chat", json={
            "message": "Second message",
            "conversation_id": user_a_conversation.id
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["conversation_id"] == user_a_conversation.id

        # Verify history was loaded (sent to AI implicitly, but we can verify DB messages count)
        assert len(user_a_conversation.messages) == 4

    def test_chat_cross_user_protection(self, client, user_b, user_a_conversation):
        login(client, user_b.email)
        res = client.post("/api/assistant/chat", json={
            "message": "Hacking into user A conv",
            "conversation_id": user_a_conversation.id
        })
        assert res.status_code == 403

    def test_get_conversations(self, client, user_a, user_a_conversation):
        login(client, user_a.email)
        res = client.get("/api/assistant/conversations")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert len(data["data"]["conversations"]) == 1
        assert data["data"]["conversations"][0]["id"] == user_a_conversation.id

    def test_get_conversations_isolated(self, client, user_b, user_a_conversation):
        login(client, user_b.email)
        res = client.get("/api/assistant/conversations")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["data"]["conversations"]) == 0

    def test_get_conversation_detail(self, client, user_a, user_a_conversation):
        login(client, user_a.email)
        res = client.get(f"/api/assistant/conversations/{user_a_conversation.id}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        
        conv = data["data"]["conversation"]
        assert conv["id"] == user_a_conversation.id
        assert len(conv["messages"]) == 2
        assert conv["messages"][0]["role"] == "user"
        assert conv["messages"][1]["role"] == "assistant"

    def test_get_conversation_detail_isolated(self, client, user_b, user_a_conversation):
        login(client, user_b.email)
        res = client.get(f"/api/assistant/conversations/{user_a_conversation.id}")
        assert res.status_code == 403

    def test_chat_offline_with_context(self, client, user_a, user_a_context, monkeypatch):
        # User has a household assessment context
        login(client, user_a.email)
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")

        res = client.post("/api/assistant/chat", json={"message": "how to save water in toilet?"})
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        
        # In offline fallback, if user_context is provided, a context prefix is prepended to the response.
        response_text = data["data"]["message"]
        assert "450" in response_text
        assert "household" in response_text
        assert "Bathing" in response_text
        assert "Dual-Flush" in response_text
