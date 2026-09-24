"""
Tests for AquaWise Profile & Gamification REST API (Task 7).

Endpoints tested:
- GET /api/profile
- PUT /api/profile
- GET /api/profile/achievements

Validates:
- Authentication protection
- Profile retrieval (streak, badges, assessment count)
- Profile update (valid fields, rejecting invalid)
- Achievement status (unlocked vs locked)
- User-data isolation
"""

import pytest
from app import create_app, seed_achievements
from backend.models import (
    db, User, Assessment, Streak, Achievement, UserAchievement
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
    user = User(name="User B", email="userb@test.com", user_type="farmer")
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def user_a_data(user_a):
    streak = Streak(user_id=user_a.id, current_streak=3, longest_streak=5)
    
    a1 = Assessment(
        user_id=user_a.id,
        assessment_type="household",
        daily_consumption=200.0,
        weekly_consumption=1400.0,
        monthly_consumption=6000.0,
        water_saver_score=85
    )
    
    ach = db.session.query(Achievement).first()
    ua = UserAchievement(user_id=user_a.id, achievement_id=ach.id)
    
    db.session.add_all([streak, a1, ua])
    db.session.commit()


def login(client, email, password="Password123!"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


class TestProfileAPI:

    def test_unauthenticated_requests(self, client):
        res1 = client.get("/api/profile")
        assert res1.status_code == 401
        
        res2 = client.put("/api/profile", json={"name": "New Name"})
        assert res2.status_code == 401
        
        res3 = client.get("/api/profile/achievements")
        assert res3.status_code == 401

    def test_get_profile(self, client, user_a, user_a_data):
        login(client, user_a.email)
        res = client.get("/api/profile")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        
        profile = data["data"]["profile"]
        assert profile["name"] == "User A"
        assert profile["email"] == "usera@test.com"
        assert profile["user_type"] == "household"
        assert "password_hash" not in profile  # Sensitive field omitted
        
        assert profile["assessment_count"] == 1
        assert profile["streak"]["current_streak"] == 3
        assert profile["streak"]["longest_streak"] == 5
        assert len(profile["badges"]) == 1

    def test_update_profile_valid(self, client, user_a):
        login(client, user_a.email)
        res = client.put("/api/profile", json={
            "name": "Updated Name",
            "user_type": "farmer"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        
        profile = data["data"]["profile"]
        assert profile["name"] == "Updated Name"
        assert profile["user_type"] == "farmer"
        
        # Verify in DB
        db_user = db.session.get(User, user_a.id)
        assert db_user.name == "Updated Name"
        assert db_user.user_type == "farmer"

    def test_update_profile_invalid(self, client, user_a):
        login(client, user_a.email)
        # Invalid user_type
        res = client.put("/api/profile", json={"user_type": "alien"})
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert "user_type" in data["error"]["details"]
        
        # Invalid name
        res = client.put("/api/profile", json={"name": ""})
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert "name" in data["error"]["details"]

    def test_get_achievements(self, client, user_a, user_a_data):
        login(client, user_a.email)
        res = client.get("/api/profile/achievements")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        
        achievements = data["data"]["achievements"]
        assert len(achievements) > 0
        
        # user_a has 1 unlocked achievement
        unlocked = [a for a in achievements if a["unlocked"] is True]
        assert len(unlocked) == 1
        assert unlocked[0]["earned_at"] is not None

    def test_user_data_isolation(self, client, user_b, user_a_data):
        # user_b should not see user_a's badges or streak
        login(client, user_b.email)
        res = client.get("/api/profile")
        assert res.status_code == 200
        data = res.get_json()
        profile = data["data"]["profile"]
        assert profile["assessment_count"] == 0
        assert profile["streak"]["current_streak"] == 0
        assert len(profile["badges"]) == 0
        
        res = client.get("/api/profile/achievements")
        assert res.status_code == 200
        achievements = res.get_json()["data"]["achievements"]
        unlocked = [a for a in achievements if a["unlocked"] is True]
        assert len(unlocked) == 0
