"""Tests for health check endpoint.

These tests use their own TestClient to avoid conftest.py's autouse db fixture.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def health_client() -> TestClient:
    """Standalone test client that doesn't require database."""
    return TestClient(app)


def test_health_check_healthy(health_client: TestClient) -> None:
    """Test healthy response when all components available."""
    with (
        patch("app.api.routes.health.check_database_health", return_value="ok"),
        patch("app.api.routes.health.check_minio_health", return_value="ok"),
    ):
        response = health_client.get("/health")

    assert response.status_code == 200
    content = response.json()
    assert content["status"] == "healthy"
    assert content["database"] == "ok"
    assert content["minio"] == "ok"
    assert "timestamp" in content
    # Verify timestamp is valid ISO-8601
    datetime.fromisoformat(content["timestamp"].replace("Z", "+00:00"))


def test_health_check_database_unavailable(health_client: TestClient) -> None:
    """Test unhealthy response when database unavailable."""
    with (
        patch("app.api.routes.health.check_database_health", return_value="error"),
        patch("app.api.routes.health.check_minio_health", return_value="ok"),
    ):
        response = health_client.get("/health")

    assert response.status_code == 503
    content = response.json()
    assert content["status"] == "unhealthy"
    assert content["database"] == "error"
    assert content["minio"] == "ok"


def test_health_check_minio_unavailable(health_client: TestClient) -> None:
    """Test unhealthy response when MinIO unavailable."""
    with (
        patch("app.api.routes.health.check_database_health", return_value="ok"),
        patch("app.api.routes.health.check_minio_health", return_value="error"),
    ):
        response = health_client.get("/health")

    assert response.status_code == 503
    content = response.json()
    assert content["status"] == "unhealthy"
    assert content["database"] == "ok"
    assert content["minio"] == "error"


def test_health_check_both_unavailable(health_client: TestClient) -> None:
    """Test unhealthy response when both database and MinIO unavailable."""
    with (
        patch("app.api.routes.health.check_database_health", return_value="error"),
        patch("app.api.routes.health.check_minio_health", return_value="error"),
    ):
        response = health_client.get("/health")

    assert response.status_code == 503
    content = response.json()
    assert content["status"] == "unhealthy"
    assert content["database"] == "error"
    assert content["minio"] == "error"


def test_health_check_response_format(health_client: TestClient) -> None:
    """Test response format matches expected schema."""
    with (
        patch("app.api.routes.health.check_database_health", return_value="ok"),
        patch("app.api.routes.health.check_minio_health", return_value="ok"),
    ):
        response = health_client.get("/health")

    content = response.json()
    # Verify all required fields exist
    assert "status" in content
    assert "database" in content
    assert "minio" in content
    assert "timestamp" in content
    # Verify field values are valid
    assert content["status"] in ["healthy", "unhealthy"]
    assert content["database"] in ["ok", "error"]
    assert content["minio"] in ["ok", "error"]


def test_health_check_no_authentication_required(health_client: TestClient) -> None:
    """Test that health endpoint is accessible without authentication."""
    with (
        patch("app.api.routes.health.check_database_health", return_value="ok"),
        patch("app.api.routes.health.check_minio_health", return_value="ok"),
    ):
        # No headers provided - should still work
        response = health_client.get("/health")

    assert response.status_code == 200
