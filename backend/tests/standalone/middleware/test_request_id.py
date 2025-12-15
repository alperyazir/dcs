"""Tests for Request ID middleware.

These tests are standalone and don't require database access.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request


@pytest.fixture
def simple_app() -> FastAPI:
    """Create a simple app with just the RequestID middleware."""
    # Import inside fixture to avoid triggering app-level imports at collection time
    from app.middleware.request_id import RequestIDMiddleware

    test_app = FastAPI()
    test_app.add_middleware(RequestIDMiddleware)

    @test_app.get("/test")
    async def test_endpoint(request: Request) -> dict:
        return {"request_id": getattr(request.state, "request_id", None)}

    return test_app


@pytest.fixture
def test_client(simple_app: FastAPI) -> Generator[TestClient, None, None]:
    """Standalone test client for middleware testing."""
    with TestClient(simple_app) as client:
        yield client


class TestRequestIDMiddleware:
    """Tests for Request ID generation and propagation."""

    def test_request_id_in_response_header(self, test_client: TestClient) -> None:
        """Test that X-Request-ID header is present in response."""
        response = test_client.get("/test")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert request_id is not None
        assert len(request_id) > 0

    def test_request_id_is_valid_uuid(self, test_client: TestClient) -> None:
        """Test that X-Request-ID is a valid UUID v4."""
        response = test_client.get("/test")

        request_id = response.headers["X-Request-ID"]
        # Should not raise ValueError if valid UUID
        parsed = uuid.UUID(request_id)
        assert parsed.version == 4

    def test_unique_request_id_per_request(self, test_client: TestClient) -> None:
        """Test that each request gets a unique request ID."""
        response1 = test_client.get("/test")
        response2 = test_client.get("/test")

        request_id_1 = response1.headers["X-Request-ID"]
        request_id_2 = response2.headers["X-Request-ID"]

        assert request_id_1 != request_id_2

    def test_request_id_stored_in_request_state(self, test_client: TestClient) -> None:
        """Test that request_id is accessible in request.state."""
        response = test_client.get("/test")

        assert response.status_code == 200
        body = response.json()
        header_id = response.headers["X-Request-ID"]

        # The endpoint returns the request_id from request.state
        assert body["request_id"] == header_id

    def test_request_id_preserved_when_client_sends_it(
        self, test_client: TestClient
    ) -> None:
        """Test that client-provided X-Request-ID is preserved in response."""
        client_request_id = str(uuid.uuid4())

        response = test_client.get("/test", headers={"X-Request-ID": client_request_id})

        # Server should honor the client's request ID
        response_id = response.headers["X-Request-ID"]
        assert response_id == client_request_id

        # Also verify it's in request.state
        body = response.json()
        assert body["request_id"] == client_request_id


class TestGetRequestIDHelper:
    """Tests for the get_request_id helper function."""

    def test_get_request_id_returns_id_when_set(self) -> None:
        """Test that get_request_id returns the ID when it's set."""
        from unittest.mock import MagicMock

        from app.middleware.request_id import get_request_id

        mock_request = MagicMock()
        mock_request.state.request_id = "test-request-id-123"

        result = get_request_id(mock_request)
        assert result == "test-request-id-123"

    def test_get_request_id_returns_none_when_not_set(self) -> None:
        """Test that get_request_id returns None when not set."""
        from unittest.mock import MagicMock

        from app.middleware.request_id import get_request_id

        mock_request = MagicMock(spec=["state"])
        mock_request.state = MagicMock(spec=[])  # No request_id attribute

        result = get_request_id(mock_request)
        assert result is None
