"""Tests for the ingestion endpoint."""

import io


def test_ingest_rejects_non_pdf(client):
    """Uploading an unsupported file type should return 400."""
    fake_file = io.BytesIO(b"this is not a pdf")
    response = client.post(
        "/api/ingest",
        files={"file": ("test.txt", fake_file, "text/plain")},
        data={"department": "maintenance"},
    )
    assert response.status_code == 400
    assert "Desteklenmeyen" in response.json()["detail"]


def test_ingest_rejects_missing_department(client):
    """Uploading without department should return 422."""
    fake_file = io.BytesIO(b"%PDF-1.4 fake content")
    response = client.post(
        "/api/ingest",
        files={"file": ("test.pdf", fake_file, "application/pdf")},
    )
    assert response.status_code == 422


def test_ingest_rejects_empty_department(client):
    """Uploading with empty department should return 400."""
    fake_file = io.BytesIO(b"%PDF-1.4 fake content")
    response = client.post(
        "/api/ingest",
        files={"file": ("test.pdf", fake_file, "application/pdf")},
        data={"department": "  "},
    )
    assert response.status_code == 400
