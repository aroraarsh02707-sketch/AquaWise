"""
Tests for AquaWise Authentication REST API (Task 1).

Endpoints tested:
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET  /api/auth/me
"""

import json
import pytest
from app import create_app
from backend.models import db, User, Streak


@pytest.fixture
def app():
    """Create test application configured with an in-memory database."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client with session cookie support."""
    return app.test_client()


class TestRegisterAPI:

    def test_register_household_success(self, client):
        """Test successful registration of a household user."""
        payload = {
            "name": "Sarah Connor",
            "email": "sarah@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "user_type": "household",
        }
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 201

        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["user"]["email"] == "sarah@example.com"
        assert data["data"]["user"]["user_type"] == "household"
        assert "password_hash" not in data["data"]["user"]

        # User is automatically logged in after registration
        me_res = client.get("/api/auth/me")
        assert me_res.status_code == 200
        assert me_res.get_json()["data"]["user"]["email"] == "sarah@example.com"

    def test_register_farmer_success(self, client):
        """Test successful registration of a farmer user."""
        payload = {
            "name": "Kisan Ram",
            "email": "ram@farm.org",
            "password": "FarmerPassword123",
            "confirm_password": "FarmerPassword123",
            "user_type": "farmer",
        }
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 201
        data = res.get_json()
        assert data["data"]["user"]["user_type"] == "farmer"

    def test_register_duplicate_email_conflict(self, client):
        """Registering with an existing email returns 409 Conflict."""
        payload = {
            "name": "User One",
            "email": "duplicate@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "user_type": "household",
        }
        res1 = client.post("/api/auth/register", json=payload)
        assert res1.status_code == 201

        # Attempt to register again with same email
        res2 = client.post("/api/auth/register", json=payload)
        assert res2.status_code == 409
        data = res2.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "CONFLICT"

    def test_register_validation_missing_name(self, client):
        payload = {
            "name": "",
            "email": "noname@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "user_type": "household",
        }
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "name" in data["error"]["details"]

    def test_register_validation_password_mismatch(self, client):
        payload = {
            "name": "Test User",
            "email": "mismatch@example.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword456!",
            "user_type": "household",
        }
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 400
        data = res.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "confirm_password" in data["error"]["details"]


class TestLoginAPI:

    @pytest.fixture(autouse=True)
    def setup_user(self, app):
        """Create a standard user for login tests."""
        user = User(
            name="Login Tester",
            email="tester@example.com",
            user_type="household"
        )
        user.set_password("CorrectPassword123")
        db.session.add(user)
        db.session.commit()

    def test_login_success(self, client):
        """Valid credentials return 200 OK and establish session."""
        res = client.post("/api/auth/login", json={
            "email": "tester@example.com",
            "password": "CorrectPassword123"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["user"]["email"] == "tester@example.com"

        # Subsequent authenticated request works
        me_res = client.get("/api/auth/me")
        assert me_res.status_code == 200
        assert me_res.get_json()["data"]["user"]["email"] == "tester@example.com"

    def test_login_wrong_password(self, client):
        res = client.post("/api/auth/login", json={
            "email": "tester@example.com",
            "password": "WrongPassword999"
        })
        assert res.status_code == 401
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_non_existent_email(self, client):
        res = client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "SomePassword"
        })
        assert res.status_code == 401
        data = res.get_json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_missing_fields(self, client):
        res = client.post("/api/auth/login", json={})
        assert res.status_code == 400
        data = res.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"


class TestMeAndLogoutAPI:

    def test_me_unauthenticated_returns_401_json(self, client):
        """Unauthenticated access to /api/auth/me returns 401 JSON, not an HTML redirect."""
        res = client.get("/api/auth/me")
        assert res.status_code == 401
        data = res.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_logout_terminates_session(self, client):
        # Register and log in
        reg_payload = {
            "name": "Logout Tester",
            "email": "logout@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "user_type": "household",
        }
        client.post("/api/auth/register", json=reg_payload)

        # Confirm logged in
        assert client.get("/api/auth/me").status_code == 200

        # Logout
        logout_res = client.post("/api/auth/logout")
        assert logout_res.status_code == 200
        assert logout_res.get_json()["success"] is True

        # Now /api/auth/me must return 401
        assert client.get("/api/auth/me").status_code == 401
