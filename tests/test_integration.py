"""
Comprehensive Integration Tests for AquaWise (Task 8).

Validates end-to-end user journeys:
- CORS preflight behavior
- Registration -> Login
- Creating an assessment -> Validation -> DB Insertion
- Viewing dashboard & trends
- Getting recommendations (fallback logic)
- Chatting with Assistant
- Viewing Profile and Achievements
"""

import pytest
from app import create_app, seed_achievements
from backend.models import db, User
from tests.browser_api_client import BrowserApiTestClient

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
    return BrowserApiTestClient(app)

class TestIntegrationJourney:

    def test_cors_preflight(self, client):
        """Verify CORS headers are returned for OPTIONS preflight requests."""
        res = client.options("/api/auth/login", headers={"Origin": "http://localhost:5173"})
        # Should return 200 OK for preflight
        assert res.status_code == 200
        assert res.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
        assert res.headers.get("Access-Control-Allow-Methods") == "GET, POST, PUT, DELETE, OPTIONS"

    def test_full_user_journey(self, client, monkeypatch):
        # 1. Register a new user
        reg_payload = {
            "name": "Integration User",
            "email": "integration@test.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "user_type": "household"
        }
        res = client.post("/api/auth/register", json=reg_payload)
        assert res.status_code == 201

        # 2. Login
        res = client.post("/api/auth/login", json={
            "email": "integration@test.com",
            "password": "Password123!"
        })
        assert res.status_code == 200
        assert res.get_json()["data"]["user"]["name"] == "Integration User"

        # 3. Create Assessment
        assessment_payload = {
            "assessment_type": "household",
            "household_size": 4,
            "showers_per_day": 4.0,
            "shower_duration_minutes": 10.0,
            "toilet_uses_per_day": 12.0,
            "kitchen_usage_minutes": 30.0,
            "laundry_loads_per_week": 3,
            "vehicle_washing_frequency": 0
        }
        res = client.post("/api/assessments", json=assessment_payload)
        assert res.status_code == 201
        data = res.get_json()
        assert data["success"] is True
        assessment_id = data["data"]["id"]
        assert data["data"]["water_saver_score"] > 0

        # 4. View Dashboard
        res = client.get("/api/dashboard")
        assert res.status_code == 200
        dash_data = res.get_json()["data"]
        assert dash_data["assessment_count"] == 1
        assert dash_data["current_streak"] == 1

        # 5. Get Recommendations (Offline Mode)
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        res = client.get(f"/api/assessments/{assessment_id}/recommendations?enhance=true")
        assert res.status_code == 200
        rec_data = res.get_json()["data"]
        assert rec_data["source"] == "rule_based"
        assert rec_data["enhanced"] is False
        assert rec_data["count"] > 0

        # 6. Chat with Assistant
        res = client.post("/api/assistant/chat", json={"message": "how can I save water?"})
        assert res.status_code == 200
        chat_data = res.get_json()["data"]
        assert chat_data["source"] == "fallback"
        assert "conversation_id" in chat_data

        # 7. View Profile and check achievements
        res = client.get("/api/profile")
        assert res.status_code == 200
        profile_data = res.get_json()["data"]["profile"]
        assert profile_data["assessment_count"] == 1
        # The user should have earned at least "First Assessment" achievement
        assert len(profile_data["badges"]) >= 1

        # 8. Check Achievements API
        res = client.get("/api/profile/achievements")
        assert res.status_code == 200
        achievements = res.get_json()["data"]["achievements"]
        unlocked = [a for a in achievements if a["unlocked"]]
        assert len(unlocked) >= 1
