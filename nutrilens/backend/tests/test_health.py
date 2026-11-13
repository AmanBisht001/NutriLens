from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns metadata and navigation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data
    assert "docs" in data
    assert data["health"] == "/api/health"


def test_api_health_endpoint(client: TestClient):
    """Test primary health check endpoint /api/health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "NutriLens API"
    assert "version" in data
    assert "environment" in data
    assert data["database"] in ["connected", "disconnected"]


def test_api_v1_health_endpoint(client: TestClient):
    """Test versioned health check endpoint /api/v1/health."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "NutriLens API"
