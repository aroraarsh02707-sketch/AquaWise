import pytest
from flask.testing import FlaskClient

from app import create_app
from backend.models import db


@pytest.fixture
def app():
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


def test_cors_allows_configured_local_origin_and_rejects_arbitrary_origin(app):
    client = app.test_client()
    allowed_origins = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    )
    for origin in allowed_origins:
        allowed = client.options("/api/auth/login", headers={"Origin": origin})
        assert allowed.headers["Access-Control-Allow-Origin"] == origin
        assert allowed.headers["Access-Control-Allow-Credentials"] == "true"
        assert "X-CSRF-Token" in allowed.headers["Access-Control-Allow-Headers"]

    rejected = client.options("/api/auth/login", headers={"Origin": "https://attacker.example"})
    assert rejected.headers.get("Access-Control-Allow-Origin") is None
    assert "Origin" in rejected.headers.get("Vary", "")


def test_csrf_token_is_required_and_accepted_for_registration(app):
    client = FlaskClient(app)
    missing = client.post("/api/auth/register", json={})
    assert missing.status_code == 400
    assert missing.get_json()["error"]["code"] == "CSRF_TOKEN_INVALID"

    token_response = client.get("/api/auth/csrf")
    token = token_response.get_json()["data"]["csrf_token"]
    assert token_response.headers["Cache-Control"] == "no-store"
    accepted = client.post(
        "/api/auth/register",
        json={
            "name": "CSRF User",
            "email": "csrf@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "user_type": "household",
        },
        headers={"X-CSRF-Token": token},
    )
    assert accepted.status_code == 201
    assert "HttpOnly" in accepted.headers["Set-Cookie"]


def test_production_startup_rejects_missing_or_placeholder_configuration(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "Lax")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")

    monkeypatch.setenv("SECRET_KEY", "change-this-to-a-secure-random-secret-key")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")

    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")

    monkeypatch.setenv("SECRET_KEY", "K8pR4mN2vQ7xA5cD9eF3hJ6kL1sW0yB4")
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="CORS_ALLOWED_ORIGINS"):
        create_app("production")


def test_production_cookie_settings_for_cross_site_topology(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "K8pR4mN2vQ7xA5cD9eF3hJ6kL1sW0yB4")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "None")
    app = create_app("production")

    assert app.config["DEBUG"] is False
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "None"
    assert app.config["REMEMBER_COOKIE_SECURE"] is True
    assert app.config["REMEMBER_COOKIE_HTTPONLY"] is True
    assert app.config["REMEMBER_COOKIE_SAMESITE"] == "None"


def test_production_rejects_non_https_or_path_based_origins(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "K8pR4mN2vQ7xA5cD9eF3hJ6kL1sW0yB4")
    monkeypatch.setenv("SESSION_COOKIE_SAMESITE", "Lax")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://app.example.com")
    with pytest.raises(RuntimeError, match="HTTPS origins"):
        create_app("production")

    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://app.example.com/path")
    with pytest.raises(RuntimeError, match="HTTPS origins"):
        create_app("production")
