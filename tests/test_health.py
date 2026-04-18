"""Tests for the health check endpoint."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Root endpoint should return API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data


def test_health_endpoint():
    """Health endpoint should return component status."""
    response = client.get("/health")
    # Could be 200 (all healthy) or 503 (something down)
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "database" in data["components"]
    assert "redis" in data["components"]
