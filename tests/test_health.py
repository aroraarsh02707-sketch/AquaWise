import json
import pytest
from app import create_app

@pytest.fixture
def client():
    """Create and configure a test client."""
    app = create_app("testing")
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test that the /api/health endpoint returns 200 OK and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert data["app"] == "AquaWise"
    assert data["environment"] == "testing"
    assert "timestamp" in data

def test_root_describes_api_service(client):
    """The Flask service exposes an API root; the Vite app owns the UI entry."""
    response = client.get("/")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["app"] == "AquaWise"
    assert data["health"] == "/api/health"

def test_404_error(client):
    """Test standard 404 JSON error response."""
    response = client.get("/api/non-existent-route")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
