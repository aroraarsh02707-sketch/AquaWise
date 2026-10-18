"""
Tests for AquaWise Dashboard API (Task 5).

Endpoints tested:
- GET /api/dashboard
- GET /api/dashboard/trends

Validates:
- unauthenticated dashboard access returns 401
- dashboard empty state for a new user
- populated dashboard returns correct metrics
- trends empty state
- trends with multiple assessments are ordered chronologically
- user-data isolation (User A cannot see User B's dashboard/trends)
"""

import pytest
from datetime import datetime, timedelta, timezone
from app import create_app, seed_achievements
from tests.browser_api_client import BrowserApiTestClient
from backend.models import (
    db, User, Assessment, Streak, ConsumptionBreakdown, Recommendation
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
    return BrowserApiTestClient(app)

@pytest.fixture
def user_a(app):
    user = User(name="User A", email="usera@test.com", user_type="household")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.flush()
    streak = Streak(user_id=user.id, current_streak=5)
    db.session.add(streak)
    db.session.commit()
    return user

@pytest.fixture
def user_b(app):
    user = User(name="User B", email="userb@test.com", user_type="household")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.flush()
    streak = Streak(user_id=user.id, current_streak=0)
    db.session.add(streak)
    db.session.commit()
    return user

@pytest.fixture
def user_a_assessments(user_a):
    now = datetime.now(timezone.utc)
    # Oldest assessment
    a1 = Assessment(
        user_id=user_a.id,
        assessment_type="household",
        assessment_date=now - timedelta(days=2),
        created_at=now - timedelta(days=2),
        daily_consumption=500.0,
        weekly_consumption=3500.0,
        monthly_consumption=15000.0,
        water_saver_score=50,
    )
    # Newest assessment
    a2 = Assessment(
        user_id=user_a.id,
        assessment_type="household",
        assessment_date=now,
        created_at=now,
        daily_consumption=400.0,
        weekly_consumption=2800.0,
        monthly_consumption=12000.0,
        water_saver_score=75,
        calculation_details={
            "calculation_version": 2,
            "estimate_kind": "rough",
            "unavailable_categories": ["Laundry"],
            "incomplete_categories": [],
            "assumptions": [],
            "assumption_litres_per_day": 0,
        },
    )
    db.session.add_all([a1, a2])
    db.session.flush()

    # Add breakdowns to newest assessment
    b1 = ConsumptionBreakdown(
        assessment_id=a2.id,
        category="Toilet",
        litres_per_day=100.0,
        percentage=25.0
    )
    b2 = ConsumptionBreakdown(
        assessment_id=a2.id,
        category="Bathing",
        litres_per_day=200.0,
        percentage=50.0
    )
    
    # Add recommendations to newest assessment
    r1 = Recommendation(
        assessment_id=a2.id,
        category="Bathing",
        title="Shorter Showers",
        description="...",
        priority="high",
        source="rule_based",
        potential_saving=50.0
    )
    r2 = Recommendation(
        assessment_id=a2.id,
        category="Toilet",
        title="Dual Flush",
        description="...",
        priority="medium",
        source="rule_based",
        potential_saving=20.0
    )

    db.session.add_all([b1, b2, r1, r2])
    db.session.commit()
    return [a1, a2]


def login(client, email, password="Password123!"):
    return client.post("/api/auth/login", json={"email": email, "password": password})

class TestDashboardAPI:

    def test_unauthenticated_request_returns_401(self, client):
        res = client.get("/api/dashboard")
        assert res.status_code == 401
        
        res = client.get("/api/dashboard/trends")
        assert res.status_code == 401

    def test_dashboard_empty_state_for_new_user(self, client, user_b):
        login(client, user_b.email)
        res = client.get("/api/dashboard")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        
        payload = data["data"]
        assert payload["assessment_count"] == 0
        assert payload["latest_daily_consumption"] is None
        assert payload["latest_weekly_consumption"] is None
        assert payload["latest_monthly_consumption"] is None
        assert payload["latest_water_saver_score"] is None
        assert payload["current_streak"] == 0
        assert payload["top_category"] is None
        assert payload["recommendations"] == []

    def test_dashboard_populated_metrics(self, client, user_a, user_a_assessments):
        login(client, user_a.email)
        res = client.get("/api/dashboard")
        assert res.status_code == 200
        data = res.get_json()
        
        payload = data["data"]
        assert payload["assessment_count"] == 2
        assert payload["latest_daily_consumption"] == 400.0
        assert payload["latest_weekly_consumption"] == 2800.0
        assert payload["latest_monthly_consumption"] == 12000.0
        assert payload["latest_water_saver_score"] == 75
        assert payload["latest_assessment_id"] == user_a_assessments[1].id
        assert payload["latest_assessment_type"] == "household"
        assert payload["latest_calculation"]["unavailable_categories"] == ["Laundry"]
        assert payload["current_streak"] == 5
        assert payload["top_category"] == "Bathing"
        assert len(payload["recommendations"]) == 2
        # Verify descending sort by potential saving
        assert payload["recommendations"][0]["potential_saving"] == 50.0
        assert payload["recommendations"][1]["potential_saving"] == 20.0

    def test_saved_score_and_calculation_metadata_are_returned_without_recalculation(self, client, user_a, user_a_assessments):
        login(client, user_a.email)
        saved = user_a_assessments[1]
        response = client.get(f"/api/assessments/{saved.id}")
        assert response.status_code == 200
        assessment = response.get_json()["data"]
        assert assessment["water_saver_score"] == 75
        assert assessment["calculation"]["unavailable_categories"] == ["Laundry"]

        dashboard = client.get("/api/dashboard").get_json()["data"]
        assert dashboard["latest_water_saver_score"] == 75
        assert dashboard["latest_calculation"] == assessment["calculation"]

    def test_legacy_score_remains_unchanged_in_result_dashboard_and_history(self, client, user_a):
        login(client, user_a.email)
        now = datetime.now(timezone.utc)
        saved = Assessment(
            user_id=user_a.id,
            assessment_type="household",
            assessment_date=now,
            created_at=now,
            daily_consumption=240.0,
            weekly_consumption=1680.0,
            monthly_consumption=7200.0,
            water_saver_score=63,
            calculation_details={"daily_consumption": 240.0, "breakdown": []},
        )
        db.session.add(saved)
        db.session.commit()

        detail = client.get(f"/api/assessments/{saved.id}").get_json()["data"]
        dashboard = client.get("/api/dashboard").get_json()["data"]
        trends = client.get("/api/dashboard/trends").get_json()["data"]["trends"]
        assert detail["water_saver_score"] == 63
        assert dashboard["latest_water_saver_score"] == 63
        assert trends[-1]["water_saver_score"] == 63
        assert db.session.get(Assessment, saved.id).water_saver_score == 63

    def test_user_data_isolation(self, client, user_b, user_a_assessments):
        # User B should not see User A's data
        login(client, user_b.email)
        res = client.get("/api/dashboard")
        assert res.status_code == 200
        payload = res.get_json()["data"]
        assert payload["assessment_count"] == 0
        
        res = client.get("/api/dashboard/trends")
        assert res.status_code == 200
        payload = res.get_json()["data"]
        assert payload["trends"] == []

class TestTrendsAPI:
    
    def test_trends_empty_state(self, client, user_b):
        login(client, user_b.email)
        res = client.get("/api/dashboard/trends")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["trends"] == []

    def test_trends_chronological_ordering(self, client, user_a, user_a_assessments):
        login(client, user_a.email)
        res = client.get("/api/dashboard/trends")
        assert res.status_code == 200
        data = res.get_json()
        
        trends = data["data"]["trends"]
        assert len(trends) == 2
        # Older assessment first
        assert trends[0]["daily_consumption"] == 500.0
        assert trends[0]["water_saver_score"] == 50
        # Newer assessment second
        assert trends[1]["daily_consumption"] == 400.0
        assert trends[1]["water_saver_score"] == 75
