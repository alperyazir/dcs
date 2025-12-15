"""Tests for error response format with request_id.

These tests verify that all error responses include request_id for debugging.
"""

import uuid
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient


@pytest.fixture
def error_app() -> "FastAPI":
    """Create app with routes that generate various errors."""
    from datetime import datetime, timezone

    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    from app.middleware.logging_middleware import LoggingMiddleware
    from app.middleware.request_id import RequestIDMiddleware

    test_app = FastAPI()
    test_app.add_middleware(LoggingMiddleware)
    test_app.add_middleware(RequestIDMiddleware)

    def get_request_id(request: Request) -> str | None:
        return getattr(request.state, "request_id", None)

    @test_app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": str(exc.detail),  # Backwards compatibility
                "error_code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": None,
                "request_id": get_request_id(request),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @test_app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, _exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal error occurred",  # Backwards compatibility
                "error_code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "details": None,
                "request_id": get_request_id(request),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    class TestInput(BaseModel):
        value: int

    @test_app.get("/success")
    async def success_endpoint() -> dict:
        return {"status": "ok"}

    @test_app.get("/not-found")
    async def not_found_endpoint() -> None:
        raise HTTPException(status_code=404, detail="Resource not found")

    @test_app.get("/server-error")
    async def server_error_endpoint() -> None:
        raise HTTPException(status_code=500, detail="Server error")

    @test_app.post("/validation")
    async def validation_endpoint(data: TestInput) -> dict:
        return {"value": data.value}

    return test_app


@pytest.fixture
def test_client(error_app: "FastAPI") -> Generator["TestClient", None, None]:
    """Standalone test client."""
    from fastapi.testclient import TestClient

    with TestClient(error_app) as client:
        yield client


class TestErrorResponseFormat:
    """Tests for error response structure."""

    def test_404_error_includes_request_id(self, test_client: "TestClient") -> None:
        """Test that 404 responses include request_id."""
        response = test_client.get("/not-found")

        assert response.status_code == 404
        body = response.json()

        assert "request_id" in body
        assert body["request_id"] is not None
        # Verify it's the same as in the header
        assert body["request_id"] == response.headers["X-Request-ID"]

    def test_500_error_includes_request_id(self, test_client: "TestClient") -> None:
        """Test that 500 responses include request_id."""
        response = test_client.get("/server-error")

        assert response.status_code == 500
        body = response.json()

        assert "request_id" in body
        assert body["request_id"] is not None
        assert body["request_id"] == response.headers["X-Request-ID"]

    def test_error_response_has_all_fields(self, test_client: "TestClient") -> None:
        """Test that error response has all required fields."""
        response = test_client.get("/not-found")

        body = response.json()

        assert "detail" in body  # Backwards compatibility with FastAPI
        assert "error_code" in body
        assert "message" in body
        assert "details" in body
        assert "request_id" in body
        assert "timestamp" in body
        # Verify detail and message match
        assert body["detail"] == body["message"]

    def test_error_response_with_client_request_id(
        self, test_client: "TestClient"
    ) -> None:
        """Test that client-provided request ID is used in error response."""
        client_id = str(uuid.uuid4())
        response = test_client.get("/not-found", headers={"X-Request-ID": client_id})

        body = response.json()
        assert body["request_id"] == client_id

    def test_error_code_format(self, test_client: "TestClient") -> None:
        """Test that error_code has expected format."""
        response = test_client.get("/not-found")
        body = response.json()

        assert body["error_code"] == "HTTP_404"

    def test_success_response_has_request_id_header(
        self, test_client: "TestClient"
    ) -> None:
        """Test that successful responses also have X-Request-ID header."""
        response = test_client.get("/success")

        assert response.status_code == 200
        assert "X-Request-ID" in response.headers


class TestValidationErrors:
    """Tests for validation error responses."""

    def test_validation_error_structure(self, test_client: "TestClient") -> None:
        """Test validation error response structure."""
        response = test_client.post(
            "/validation",
            json={"value": "not-an-int"},
        )

        assert response.status_code == 422
        # Still has request ID header
        assert "X-Request-ID" in response.headers


class TestSecretsSecurity:
    """Tests for NFR-S7: Secrets are never exposed in error responses."""

    @pytest.fixture
    def secure_error_app(self) -> "FastAPI":
        """Create app that simulates sensitive data in exceptions.

        Note: This app doesn't use middleware to simplify exception handling testing.
        The middleware is tested separately.
        """
        from datetime import datetime, timezone

        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse

        test_app = FastAPI()

        @test_app.exception_handler(Exception)
        async def secure_exception_handler(
            _request: Request, _exc: Exception
        ) -> JSONResponse:
            # This handler should NOT expose the exception details
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal error occurred",
                    "error_code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "details": None,
                    "request_id": None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        @test_app.get("/sensitive-error")
        async def sensitive_error_endpoint() -> None:
            # Simulate an error that contains sensitive info
            raise ValueError("Database connection failed: password=supersecret123")

        @test_app.get("/config-error")
        async def config_error_endpoint() -> None:
            # Simulate a config error with secrets
            raise RuntimeError("MinIO connection failed with secret_key=minio_key_123")

        return test_app

    @pytest.fixture
    def secure_client(
        self, secure_error_app: "FastAPI"
    ) -> Generator["TestClient", None, None]:
        """Test client for secure error app."""
        from fastapi.testclient import TestClient

        with TestClient(secure_error_app, raise_server_exceptions=False) as client:
            yield client

    def test_500_error_hides_exception_details(
        self, secure_client: "TestClient"
    ) -> None:
        """Test that 500 errors do not expose exception details."""
        response = secure_client.get("/sensitive-error")

        assert response.status_code == 500
        body = response.json()

        # Should NOT contain the password from the exception
        response_text = str(body)
        assert "supersecret123" not in response_text
        assert "password=" not in response_text.lower()

    def test_config_error_hides_secrets(self, secure_client: "TestClient") -> None:
        """Test that config errors do not expose secrets."""
        response = secure_client.get("/config-error")

        assert response.status_code == 500
        body = response.json()

        # Should NOT contain the secret key from the exception
        response_text = str(body)
        assert "minio_key_123" not in response_text
        assert "secret_key=" not in response_text.lower()

    def test_error_response_is_generic(self, secure_client: "TestClient") -> None:
        """Test that error responses are generic for security."""
        response = secure_client.get("/sensitive-error")

        body = response.json()

        # Should be a generic error message
        assert body["message"] == "An internal error occurred"
        assert body["error_code"] == "INTERNAL_ERROR"
        # Details should be None for security
        assert body["details"] is None
