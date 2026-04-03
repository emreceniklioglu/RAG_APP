"""Tests for the health endpoint."""


def test_health_returns_200(client):
    """Health endpoint should return 200 with status healthy."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "vector_store_chunks" in data


def test_health_has_service_name(client):
    """Health response should include service name."""
    response = client.get("/api/health")
    data = response.json()
    assert "service" in data
    assert len(data["service"]) > 0
