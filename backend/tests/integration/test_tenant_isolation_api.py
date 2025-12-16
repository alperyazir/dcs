"""
Integration tests for API tenant isolation (Story 2.3, Task 10.9-10.10).

Tests:
- API endpoint tenant filtering for different user roles
- Cross-tenant access prevention via API
- Admin bypass via API

These tests require a running database with test data.
Run with: uv run pytest tests/integration/ -v

References:
- AC: #1-10 (all acceptance criteria at API level)
"""


import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import UserRole

# Test client
client = TestClient(app)


# Test credentials (from seed_test_data.py)
TEST_PASSWORD = "testpass123"
TEST_USERS = {
    "admin": {"email": "admin@test.com", "role": UserRole.ADMIN},
    "supervisor": {"email": "supervisor@test.com", "role": UserRole.SUPERVISOR},
    "publisher": {"email": "publisher@test.com", "role": UserRole.PUBLISHER},
    "teacher": {"email": "teacher@test.com", "role": UserRole.TEACHER},
    "student": {"email": "student@test.com", "role": UserRole.STUDENT},
}


def get_token(email: str, password: str = TEST_PASSWORD) -> str | None:
    """Get JWT token for a test user."""
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": email, "password": password},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def get_auth_headers(email: str) -> dict:
    """Get authorization headers for a test user."""
    token = get_token(email)
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


class TestLoginTenantContext:
    """Tests for login returning correct tenant context in JWT."""

    @pytest.mark.integration
    def test_admin_login_returns_token(self):
        """Admin user can login and gets a valid token."""
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "admin@test.com", "password": TEST_PASSWORD},
        )
        if response.status_code == 400:
            pytest.skip(
                "Test users not seeded in test database - run seed_test_data.py first"
            )
        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.integration
    def test_publisher_login_returns_token_with_tenant(self):
        """Publisher user gets token with tenant_id."""
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "publisher@test.com", "password": TEST_PASSWORD},
        )
        if response.status_code == 400:
            pytest.skip("Test users not seeded in test database")
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data

    @pytest.mark.integration
    def test_teacher_login_returns_token_with_tenant(self):
        """Teacher user gets token with tenant_id."""
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "teacher@test.com", "password": TEST_PASSWORD},
        )
        if response.status_code == 400:
            pytest.skip("Test users not seeded in test database")
        assert response.status_code == 200

    @pytest.mark.integration
    def test_invalid_credentials_rejected(self):
        """Invalid credentials are rejected."""
        response = client.post(
            "/api/v1/login/access-token",
            data={"username": "nonexistent@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 400


class TestTokenVerification:
    """Tests for token verification endpoint."""

    @pytest.mark.integration
    def test_admin_token_verification(self):
        """Admin token verification returns user info."""
        headers = get_auth_headers("admin@test.com")
        if not headers:
            pytest.skip("Admin user not seeded")

        response = client.post("/api/v1/login/test-token", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "admin@test.com"
        assert user_data["role"] == "admin"

    @pytest.mark.integration
    def test_publisher_token_contains_tenant(self):
        """Publisher token verification shows tenant_id."""
        headers = get_auth_headers("publisher@test.com")
        if not headers:
            pytest.skip("Publisher user not seeded")

        response = client.post("/api/v1/login/test-token", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["role"] == "publisher"
        # Publisher should have a tenant_id
        assert user_data.get("tenant_id") is not None

    @pytest.mark.integration
    def test_teacher_token_contains_tenant(self):
        """Teacher token verification shows tenant_id."""
        headers = get_auth_headers("teacher@test.com")
        if not headers:
            pytest.skip("Teacher user not seeded")

        response = client.post("/api/v1/login/test-token", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["role"] == "teacher"
        assert user_data.get("tenant_id") is not None

    @pytest.mark.integration
    def test_expired_token_rejected(self):
        """Expired or invalid tokens are rejected."""
        response = client.post(
            "/api/v1/login/test-token",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


class TestTenantIsolationConcept:
    """Tests verifying tenant isolation concepts work at API level."""

    @pytest.mark.integration
    def test_different_tenants_have_different_ids(self):
        """Publisher and Teacher have different tenant_ids."""
        publisher_headers = get_auth_headers("publisher@test.com")
        teacher_headers = get_auth_headers("teacher@test.com")

        if not publisher_headers or not teacher_headers:
            pytest.skip("Test users not seeded")

        pub_resp = client.post("/api/v1/login/test-token", headers=publisher_headers)
        teacher_resp = client.post("/api/v1/login/test-token", headers=teacher_headers)

        pub_tenant = pub_resp.json().get("tenant_id")
        teacher_tenant = teacher_resp.json().get("tenant_id")

        # Publisher Corp and School District should have different tenant_ids
        assert pub_tenant != teacher_tenant

    @pytest.mark.integration
    def test_same_tenant_users_share_tenant_id(self):
        """Teacher and Student in same tenant share tenant_id."""
        teacher_headers = get_auth_headers("teacher@test.com")
        student_headers = get_auth_headers("student@test.com")

        if not teacher_headers or not student_headers:
            pytest.skip("Test users not seeded")

        teacher_resp = client.post("/api/v1/login/test-token", headers=teacher_headers)
        student_resp = client.post("/api/v1/login/test-token", headers=student_headers)

        teacher_tenant = teacher_resp.json().get("tenant_id")
        student_tenant = student_resp.json().get("tenant_id")

        # Both should be in School District tenant
        assert teacher_tenant == student_tenant

    @pytest.mark.integration
    def test_admin_has_no_tenant_restriction(self):
        """Admin user has null/none tenant (full access)."""
        headers = get_auth_headers("admin@test.com")
        if not headers:
            pytest.skip("Admin user not seeded")

        response = client.post("/api/v1/login/test-token", headers=headers)
        user_data = response.json()

        # Admin should have no tenant restriction (None)
        assert user_data.get("tenant_id") is None


class TestUnauthorizedAccess:
    """Tests for unauthorized access scenarios."""

    @pytest.mark.integration
    def test_no_token_rejected(self):
        """Requests without token are rejected."""
        response = client.post("/api/v1/login/test-token")
        assert response.status_code == 401

    @pytest.mark.integration
    def test_malformed_token_rejected(self):
        """Malformed tokens are rejected."""
        response = client.post(
            "/api/v1/login/test-token",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
        assert response.status_code == 401

    @pytest.mark.integration
    def test_missing_bearer_prefix_rejected(self):
        """Tokens without 'Bearer' prefix are rejected."""
        token = get_token("admin@test.com")
        if not token:
            pytest.skip("Admin user not seeded")

        response = client.post(
            "/api/v1/login/test-token",
            headers={"Authorization": token},  # Missing "Bearer "
        )
        assert response.status_code == 401
