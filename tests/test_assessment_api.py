"""
Tests for AquaWise Assessment REST API (Task 3).

Endpoints tested:
- POST   /api/assessments      : Create and calculate new assessment
- GET    /api/assessments      : Historical assessments list for current user
- GET    /api/assessments/<id> : Detailed assessment retrieval with breakdown & recommendations
- DELETE /api/assessments/<id> : Deletion of assessment with cascading cleanup

Validates:
- Validation errors handling
- Deterministic calculation persistence
- Water Saver Score integration
- Streak and achievement awards
- Strict tenant data isolation (User A cannot access or delete User B's records)
- Unauthenticated access rejection (401 JSON)
- Cascading delete cleanup
"""

import pytest
from app import create_app, seed_achievements
from backend.models import (
    db,
    User,
    Assessment,
    HouseholdUsageDetails,
    FarmerUsageDetails,
    ConsumptionBreakdown,
    Recommendation,
    Streak,
    UserAchievement,
)


@pytest.fixture
def app():
    """Create test application with isolated in-memory database."""
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
    """Primary household user."""
    user = User(name="Alice Household", email="alice@test.com", user_type="household")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.flush()
    streak = Streak(user_id=user.id)
    db.session.add(streak)
    db.session.commit()
    return user


@pytest.fixture
def user_b(app):
    """Secondary farmer user for isolation checks."""
    user = User(name="Bob Farmer", email="bob@test.com", user_type="farmer")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.flush()
    streak = Streak(user_id=user.id)
    db.session.add(streak)
    db.session.commit()
    return user


def login_client(client, email, password="Password123!"):
    """Helper to authenticate a test client session."""
    return client.post("/api/auth/login", json={"email": email, "password": password})


class TestCreateAssessmentAPI:

    def test_unauthenticated_create_rejected(self, client):
        """Unauthenticated POST returns 401 UNAUTHORIZED."""
        res = client.post("/api/assessments", json={})
        assert res.status_code == 401
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_create_household_assessment_success(self, client, user_a):
        """Valid household assessment calculates, scores, awards achievements, and persists."""
        login_client(client, user_a.email)

        payload = {
            "assessment_type": "household",
            "household_size": 3,
            "showers_per_day": 2,
            "shower_duration_minutes": 8,
            "toilet_uses_per_day": 4,
            "laundry_loads_per_week": 3,
            "kitchen_usage_minutes": 20,
            "vehicle_washing_frequency": 1,
            "gardening_frequency": 2,
            "gardening_duration_minutes": 15,
            "other_usage_litres": 5,
        }
        res = client.post("/api/assessments", json=payload)
        assert res.status_code == 201

        data = res.get_json()
        assert data["success"] is True
        assessment = data["data"]
        assert assessment["user_id"] == user_a.id
        assert assessment["assessment_type"] == "household"
        assert abs(assessment["weekly_consumption"] - assessment["daily_consumption"] * 7) <= 1.0
        assert abs(assessment["monthly_consumption"] - assessment["daily_consumption"] * 30) <= 2.0
        assert 0 <= assessment["water_saver_score"] <= 100

        # Verify usage details, breakdown, and baseline recommendations are included
        assert assessment["details"]["household_size"] == 3
        assert len(assessment["breakdown"]) >= 5
        assert len(assessment["recommendations"]) >= 1

        # Verify streak update
        assert assessment["streak"]["current_streak"] >= 1

        # Verify achievement evaluation awarded "First Assessment"
        new_badges = [a["name"] for a in assessment["new_achievements"]]
        assert "First Assessment" in new_badges

    def test_create_farmer_assessment_success(self, client, user_b):
        """Valid agricultural assessment calculates and persists with farmer details."""
        login_client(client, user_b.email)

        payload = {
            "assessment_type": "farmer",
            "farm_area": 4.0,
            "farm_area_unit": "acre",
            "crop_type": "wheat",
            "irrigation_method": "drip",
            "irrigation_frequency": 3,
            "irrigation_duration_minutes": 60,
            "water_source": "canal",
            "rainwater_harvesting": True,
            "estimated_irrigation_litres": 1500.0,
        }
        res = client.post("/api/assessments", json=payload)
        assert res.status_code == 201

        data = res.get_json()
        assert data["success"] is True
        assessment = data["data"]
        assert assessment["user_id"] == user_b.id
        assert assessment["assessment_type"] == "farmer"
        assert assessment["details"]["crop_type"] == "wheat"
        assert assessment["details"]["irrigation_method"] == "drip"
        assert assessment["details"]["rainwater_harvesting"] is True

    def test_create_assessment_validation_failure(self, client, user_a):
        """Invalid inputs return 400 with VALIDATION_ERROR."""
        login_client(client, user_a.email)

        # Invalid zero household size
        payload = {
            "assessment_type": "household",
            "household_size": 0,
            "showers_per_day": 1,
            "shower_duration_minutes": 5,
            "toilet_uses_per_day": 4,
            "laundry_loads_per_week": 2,
            "kitchen_usage_minutes": 15,
        }
        res = client.post("/api/assessments", json=payload)
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "household_size" in data["error"]["details"]


class TestAssessmentHistoryAPI:

    def test_get_assessments_empty_history(self, client, user_a):
        login_client(client, user_a.email)
        res = client.get("/api/assessments")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["assessments"] == []
        assert data["data"]["pagination"]["total"] == 0

    def test_get_assessments_lists_only_current_user_assessments(self, client, user_a, user_b):
        # Create assessment for user_a
        login_client(client, user_a.email)
        client.post("/api/assessments", json={
            "assessment_type": "household",
            "household_size": 2,
            "showers_per_day": 1,
            "shower_duration_minutes": 5,
            "toilet_uses_per_day": 4,
            "laundry_loads_per_week": 2,
            "kitchen_usage_minutes": 15,
        })

        # Create assessment for user_b
        login_client(client, user_b.email)
        client.post("/api/assessments", json={
            "assessment_type": "farmer",
            "farm_area": 2.0,
            "farm_area_unit": "acre",
            "crop_type": "corn",
            "irrigation_method": "flood",
            "irrigation_frequency": 2,
            "irrigation_duration_minutes": 60,
        })

        # User A's history must show exactly 1 assessment, belonging to user_a
        login_client(client, user_a.email)
        res_a = client.get("/api/assessments")
        assert res_a.status_code == 200
        items_a = res_a.get_json()["data"]["assessments"]
        assert len(items_a) == 1
        assert items_a[0]["user_id"] == user_a.id

        # User B's history must show exactly 1 assessment, belonging to user_b
        login_client(client, user_b.email)
        res_b = client.get("/api/assessments")
        assert res_b.status_code == 200
        items_b = res_b.get_json()["data"]["assessments"]
        assert len(items_b) == 1
        assert items_b[0]["user_id"] == user_b.id


class TestAssessmentDetailAndPrivacyAPI:

    @pytest.fixture
    def user_a_assessment(self, client, user_a):
        login_client(client, user_a.email)
        res = client.post("/api/assessments", json={
            "assessment_type": "household",
            "household_size": 2,
            "showers_per_day": 2,
            "shower_duration_minutes": 6,
            "toilet_uses_per_day": 5,
            "laundry_loads_per_week": 3,
            "kitchen_usage_minutes": 20,
        })
        return res.get_json()["data"]["id"]

    def test_get_assessment_detail_success(self, client, user_a, user_a_assessment):
        login_client(client, user_a.email)
        res = client.get(f"/api/assessments/{user_a_assessment}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == user_a_assessment
        assert data["data"]["details"] is not None
        assert len(data["data"]["breakdown"]) > 0

    def test_get_assessment_not_found(self, client, user_a):
        login_client(client, user_a.email)
        res = client.get("/api/assessments/99999")
        assert res.status_code == 404
        assert res.get_json()["error"]["code"] == "NOT_FOUND"

    def test_user_cannot_access_another_users_assessment(self, client, user_b, user_a_assessment):
        """User B attempting to view User A's assessment gets 403 FORBIDDEN."""
        login_client(client, user_b.email)
        res = client.get(f"/api/assessments/{user_a_assessment}")
        assert res.status_code == 403
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    def test_user_cannot_delete_another_users_assessment(self, client, user_a, user_b, user_a_assessment):
        """User B attempting to delete User A's assessment gets 403 FORBIDDEN."""
        login_client(client, user_b.email)
        res = client.delete(f"/api/assessments/{user_a_assessment}")
        assert res.status_code == 403
        assert res.get_json()["error"]["code"] == "FORBIDDEN"

        # Verify assessment was NOT deleted
        login_client(client, user_a.email)
        check_res = client.get(f"/api/assessments/{user_a_assessment}")
        assert check_res.status_code == 200

    def test_delete_assessment_success_and_cascade_cleanup(self, client, user_a, user_a_assessment):
        """Deleting an assessment removes it and all associated details and recommendations."""
        login_client(client, user_a.email)

        # Confirm existence
        assert db.session.get(Assessment, user_a_assessment) is not None
        assert HouseholdUsageDetails.query.filter_by(assessment_id=user_a_assessment).first() is not None
        assert ConsumptionBreakdown.query.filter_by(assessment_id=user_a_assessment).count() > 0
        assert Recommendation.query.filter_by(assessment_id=user_a_assessment).count() > 0

        # Delete
        del_res = client.delete(f"/api/assessments/{user_a_assessment}")
        assert del_res.status_code == 200
        assert del_res.get_json()["success"] is True

        # Verify cascade deletion in database
        assert db.session.get(Assessment, user_a_assessment) is None
        assert HouseholdUsageDetails.query.filter_by(assessment_id=user_a_assessment).first() is None
        assert ConsumptionBreakdown.query.filter_by(assessment_id=user_a_assessment).count() == 0
        assert Recommendation.query.filter_by(assessment_id=user_a_assessment).count() == 0
