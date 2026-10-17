"""
Tests for AquaWise Recommendation REST API (Task 4).

Endpoints tested:
- GET /api/assessments/<id>/recommendations
- GET /api/assessments/<id>/recommendations?enhance=true

Validates:
- Unauthenticated access returns 401
- Non-existent assessment returns 404
- Cross-user ownership protection returns 403
- Valid retrieval of stored recommendations
- Empty recommendation list handling
- AI enhancement (?enhance=true) personalizes wording while strictly preserving deterministic savings and priorities
- Graceful offline / error fallback for AI enhancement
"""

import json
from unittest.mock import patch, MagicMock
import pytest
import requests
from app import create_app, seed_achievements
from backend.models import (
    db,
    User,
    Assessment,
    HouseholdUsageDetails,
    ConsumptionBreakdown,
    Recommendation,
    Streak,
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
    db.session.flush()
    streak = Streak(user_id=user.id)
    db.session.add(streak)
    db.session.commit()
    return user


@pytest.fixture
def user_b(app):
    user = User(name="User B", email="userb@test.com", user_type="household")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.flush()
    streak = Streak(user_id=user.id)
    db.session.add(streak)
    db.session.commit()
    return user


@pytest.fixture
def assessment_with_recs(user_a):
    """Create a populated assessment for User A with usage details, breakdown, and recommendations."""
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

    details = HouseholdUsageDetails(
        assessment_id=assessment.id,
        household_size=3,
        showers_per_day=2.0,
        shower_duration_minutes=10.0,
        toilet_uses_per_day=4.0,
        kitchen_usage_minutes=25.0,
        vehicle_washing_frequency=1.0,
    )
    b1 = ConsumptionBreakdown(
        assessment_id=assessment.id,
        category="Bathing",
        litres_per_day=270.0,
        percentage=60.0
    )
    b2 = ConsumptionBreakdown(
        assessment_id=assessment.id,
        category="Toilet",
        litres_per_day=72.0,
        percentage=16.0
    )
    r1 = Recommendation(
        assessment_id=assessment.id,
        category="Bathing",
        title="Reduce Shower Time & Install Aerators",
        description="Reducing showers to 5 minutes saves significant water.",
        priority="high",
        source="rule_based",
        potential_saving=45.0,
    )
    r2 = Recommendation(
        assessment_id=assessment.id,
        category="Toilet",
        title="Install Dual-Flush Cistern",
        description="Dual flush cuts water use per flush by 40%.",
        priority="medium",
        source="rule_based",
        potential_saving=24.0,
    )
    db.session.add_all([details, b1, b2, r1, r2])
    db.session.commit()
    return assessment


@pytest.fixture
def assessment_empty_recs(user_a):
    """Assessment for User A with no recommendations."""
    assessment = Assessment(
        user_id=user_a.id,
        assessment_type="household",
        daily_consumption=100.0,
        weekly_consumption=700.0,
        monthly_consumption=3000.0,
        water_saver_score=90,
    )
    db.session.add(assessment)
    db.session.commit()
    return assessment


def login(client, email, password="Password123!"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


class TestRecommendationRetrievalAPI:

    def test_unauthenticated_request_returns_401(self, client, assessment_with_recs):
        res = client.get(f"/api/assessments/{assessment_with_recs.id}/recommendations")
        assert res.status_code == 401
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_non_existent_assessment_returns_404(self, client, user_a):
        login(client, user_a.email)
        res = client.get("/api/assessments/99999/recommendations")
        assert res.status_code == 404
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_cross_user_access_returns_403(self, client, user_b, assessment_with_recs):
        """User B cannot view recommendations for User A's assessment."""
        login(client, user_b.email)
        res = client.get(f"/api/assessments/{assessment_with_recs.id}/recommendations")
        assert res.status_code == 403
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_retrieve_stored_recommendations_success(self, client, user_a, assessment_with_recs):
        """Owner retrieves stored recommendations in clean JSON."""
        login(client, user_a.email)
        res = client.get(f"/api/assessments/{assessment_with_recs.id}/recommendations")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        payload = data["data"]
        assert payload["assessment_id"] == assessment_with_recs.id
        assert payload["count"] == 2
        assert payload["enhanced"] is False

        recs = payload["recommendations"]
        assert len(recs) == 2
        # Check preserved fields
        assert recs[0]["category"] == "Bathing"
        assert recs[0]["priority"] == "high"
        assert recs[0]["potential_saving"] == 45.0
        assert recs[0]["source"] == "rule_based"

    def test_recommendation_without_savings_remains_retrievable(self, client, user_a, assessment_with_recs):
        """Action-only recommendations have no savings estimate and still sort safely."""
        assessment_with_recs.recommendations[0].potential_saving = None
        db.session.commit()
        login(client, user_a.email)

        response = client.get(f"/api/assessments/{assessment_with_recs.id}/recommendations")
        assert response.status_code == 200
        items = response.get_json()["data"]["recommendations"]
        assert len(items) == 2
        assert items[0]["potential_saving"] == 45.0
        assert items[1]["potential_saving"] is None

    def test_empty_recommendation_result(self, client, user_a, assessment_empty_recs):
        """Assessment with no recommendations returns clean empty list."""
        login(client, user_a.email)
        res = client.get(f"/api/assessments/{assessment_empty_recs.id}/recommendations")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["count"] == 0
        assert data["data"]["recommendations"] == []

    @patch("backend.services.ai_service.requests.post")
    def test_enhance_true_with_ai_success(self, mock_post, client, user_a, assessment_with_recs, monkeypatch):
        """When enhance=true and AI succeeds, wording is personalized while numbers are strictly preserved."""
        login(client, user_a.email)
        monkeypatch.setenv("AI_API_KEY", "test-ai-key")

        # Mock AI response
        ai_personalized = [
            {
                "category": "Bathing",
                "title": "Family Shower Timing Challenge",
                "description": "Shorten everyone's shower by 3 minutes to save massive water daily!",
                "priority": "high",
                "potential_saving": 9999.0,  # Deliberate invalid number to verify guardrail
            }
        ]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": f"```json\n{json.dumps(ai_personalized)}\n```"}]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        res = client.get(f"/api/assessments/{assessment_with_recs.id}/recommendations?enhance=true")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        payload = data["data"]
        assert payload["enhanced"] is True
        assert payload["source"] == "hybrid"

        recs = payload["recommendations"]
        # AI personalized title is present
        assert recs[0]["title"] == "Family Shower Timing Challenge"
        # CRITICAL TEST: Potential saving is preserved from deterministic rule, NOT AI hallucinated number!
        assert recs[0]["potential_saving"] != 9999.0
        assert recs[0]["potential_saving"] > 0
        assert recs[0]["priority"] == "high"

    @patch("backend.services.ai_service.requests.post")
    def test_enhance_true_ai_failure_fallback(self, mock_post, client, user_a, assessment_with_recs, monkeypatch):
        """When AI service fails during ?enhance=true, gracefully falls back to deterministic recommendations."""
        login(client, user_a.email)
        monkeypatch.setenv("AI_API_KEY", "test-ai-key")
        mock_post.side_effect = requests.RequestException("Google Gemini API unreachable")

        res = client.get(f"/api/assessments/{assessment_with_recs.id}/recommendations?enhance=true")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        payload = data["data"]
        # Falls back to rule_based
        assert payload["enhanced"] is False
        assert payload["source"] == "rule_based"
        assert len(payload["recommendations"]) >= 1
        assert all(r["source"] == "rule_based" for r in payload["recommendations"])

    def test_enhance_true_in_offline_mode(self, client, user_a, assessment_with_recs, monkeypatch):
        """When no AI API key is set, ?enhance=true returns rule-based recommendations without error."""
        login(client, user_a.email)
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")

        res = client.get(f"/api/assessments/{assessment_with_recs.id}/recommendations?enhance=true")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["enhanced"] is False
        assert data["data"]["source"] == "rule_based"
