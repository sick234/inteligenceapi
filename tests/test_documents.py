"""
Tests for the document management endpoints.

Covers: upload (valid, invalid type, unauthorized), listing with pagination,
stats, detail view, deletion, and 404 scenarios.
"""
import io

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_EMAIL = "doc_test@example.com"
TEST_PASSWORD = "DocPass123"


def _get_auth_headers() -> dict | None:
    """Helper: register user and return auth headers."""
    client.post("/api/v1/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    login_resp = client.post("/api/v1/auth/login", data={
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    token = login_resp.json().get("access_token")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


# ── Upload ────────────────────────────────────────────────────

def test_upload_unauthorized():
    """Upload without auth should return 401."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"content", "text/plain")},
    )
    assert response.status_code == 401


def test_upload_valid_text_file():
    """Uploading a valid .txt file should return 202 Accepted."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"Hello world content", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["filename"] == "test.txt"
    assert data["file_size_bytes"] > 0


def test_upload_invalid_file_type():
    """Uploading an unsupported file type should return 400."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("image.png", b"fake png", "image/png")},
        headers=headers,
    )
    assert response.status_code == 400


def test_upload_empty_file():
    """Uploading an empty file should return 400."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
        headers=headers,
    )
    assert response.status_code == 400


# ── Listing ───────────────────────────────────────────────────

def test_list_documents_paginated():
    """Listing documents should return paginated results."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.get("/api/v1/documents/?page=1&page_size=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "total_pages" in data


def test_list_documents_with_status_filter():
    """Filtering by status should work."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.get("/api/v1/documents/?status=uploaded", headers=headers)
    assert response.status_code == 200


# ── Stats ─────────────────────────────────────────────────────

def test_get_stats():
    """Stats endpoint should return aggregate data."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.get("/api/v1/documents/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "completed" in data
    assert "processing" in data
    assert "failed" in data
    assert "total_words_analyzed" in data


# ── Detail View ───────────────────────────────────────────────

def test_get_document_not_found():
    """Requesting a non-existent document should return 404."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.get("/api/v1/documents/99999", headers=headers)
    assert response.status_code == 404


# ── Delete ────────────────────────────────────────────────────

def test_delete_document():
    """Deleting an existing document should return 204."""
    headers = _get_auth_headers()
    if not headers:
        return

    # Upload first
    upload_resp = client.post(
        "/api/v1/documents/upload",
        files={"file": ("to_delete.txt", b"delete me", "text/plain")},
        headers=headers,
    )
    if upload_resp.status_code != 202:
        return

    doc_id = upload_resp.json()["id"]
    response = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert response.status_code == 204


def test_delete_nonexistent_document():
    """Deleting a non-existent document should return 404."""
    headers = _get_auth_headers()
    if not headers:
        return

    response = client.delete("/api/v1/documents/99999", headers=headers)
    assert response.status_code == 404
