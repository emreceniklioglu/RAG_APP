"""Tests for the query endpoint."""


def test_query_rejects_invalid_role(client):
    """Querying with an invalid role should return 400."""
    response = client.post(
        "/api/query",
        json={"question": "Test sorusu", "user_role": "nonexistent_role"},
    )
    assert response.status_code == 400
    assert "Geçersiz" in response.json()["detail"]


def test_query_rejects_empty_question(client):
    """Querying with empty question should return 422 (Pydantic validation)."""
    response = client.post(
        "/api/query",
        json={"question": "", "user_role": "engineer"},
    )
    assert response.status_code == 422


def test_query_rejects_missing_fields(client):
    """Querying without required fields should return 422."""
    response = client.post("/api/query", json={})
    assert response.status_code == 422


def test_documents_endpoint_returns_list(client):
    """Documents endpoint should return a list (possibly empty)."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "documents" in data
    assert isinstance(data["documents"], list)
