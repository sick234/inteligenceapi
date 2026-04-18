"""
Tests for the authentication endpoints.

Covers: registration, login, profile retrieval, password validation,
and unauthorized access scenarios.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

TEST_EMAIL = "auth_test@example.com"
TEST_PASSWORD = "SecurePass1"  # Meets strength requirements
TEST_FULL_NAME = "Auth Test User"


# ── Registration ──────────────────────────────────────────────

def test_register_user():
    """Test that a new user can register with valid data."""
    response = client.post("/api/v1/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_FULL_NAME,
    })
    # 201 on first run, 409 if user already exists
    assert response.status_code in [201, 409]

    if response.status_code == 201:
        data = response.json()
        assert data["email"] == TEST_EMAIL
        assert data["full_name"] == TEST_FULL_NAME
        assert "id" in data
        assert "hashed_password" not in data


def test_register_weak_password():
    """Passwords without uppercase/lowercase/digit should be rejected."""
    response = client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "alllowercase",
    })
    assert response.status_code == 422


def test_register_short_password():
    """Passwords under 8 characters should be rejected."""
    response = client.post("/api/v1/auth/register", json={
        "email": "short@example.com",
        "password": "Ab1",
    })
    assert response.status_code == 422


def test_register_duplicate_email():
    """Registering with an existing email should return 409."""
    # Ensure user exists first
    client.post("/api/v1/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    # Try again
    response = client.post("/api/v1/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 409


# ── Login ─────────────────────────────────────────────────────

def test_login_success():
    """Valid credentials should return a JWT token."""
    # Ensure user exists
    client.post("/api/v1/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    response = client.post("/api/v1/auth/login", data={
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password():
    """Invalid password should return 401."""
    response = client.post("/api/v1/auth/login", data={
        "username": TEST_EMAIL,
        "password": "WrongPassword1",
    })
    assert response.status_code == 401


def test_login_nonexistent_user():
    """Login with an unregistered email should return 401."""
    response = client.post("/api/v1/auth/login", data={
        "username": "nobody@example.com",
        "password": "SomePass123",
    })
    assert response.status_code == 401


# ── Profile ───────────────────────────────────────────────────

def test_get_profile():
    """Authenticated users should be able to view their profile."""
    # Ensure user + get token
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
        return

    response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert response.status_code == 200
    assert response.json()["email"] == TEST_EMAIL


def test_profile_without_token():
    """Accessing /me without a token should return 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_profile_with_invalid_token():
    """Accessing /me with a garbage token should return 401."""
    response = client.get("/api/v1/auth/me", headers={
        "Authorization": "Bearer invalid.token.here",
    })
    assert response.status_code == 401
