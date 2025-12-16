"""
Unit tests for role-based rate limiting (Story 2.4).

Tests AC: #1-#10 for rate limiting per user role.
"""

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import Request
from slowapi.errors import RateLimitExceeded
from starlette.datastructures import Headers

from app.middleware.rate_limit import (
    RATE_LIMITS,
    get_client_ip,
    get_rate_limit_for_request,
    get_rate_limit_key,
    rate_limit_exceeded_handler,
)
from app.models import UserRole


class MockState:
    """Mock request state for testing."""

    def __init__(self) -> None:
        self.current_user: Any = None
        self.request_id: str | None = None
        self.user_id: str | None = None
        self.role: str | None = None


def create_mock_request(
    user_id: str | None = None,
    role: str | None = None,
    request_id: str | None = None,
    headers: dict[str, str] | None = None,
    path: str = "/api/v1/assets",
    method: str = "GET",
) -> MagicMock:
    """Create a mock request with optional user context."""
    request = MagicMock(spec=Request)
    state = MockState()

    if user_id and role:
        # Create current_user mock (matching TenantContextMiddleware output)
        current_user = MagicMock()
        current_user.user_id = user_id
        current_user.role = role
        state.current_user = current_user

    state.request_id = request_id or str(uuid4())
    request.state = state
    request.headers = Headers(headers or {})
    request.url = MagicMock()
    request.url.path = path
    request.method = method

    return request


class TestRateLimitConstants:
    """Test rate limit configuration constants (AC: #1, #2, #3, #4)."""

    def test_publisher_limit_is_1000_per_hour(self) -> None:
        """AC: #1 - Publishers are limited to 1000 requests per hour."""
        assert RATE_LIMITS[UserRole.PUBLISHER] == "1000/hour"

    def test_school_limit_is_1000_per_hour(self) -> None:
        """School role has same limit as publisher."""
        assert RATE_LIMITS[UserRole.SCHOOL] == "1000/hour"

    def test_teacher_limit_is_500_per_hour(self) -> None:
        """AC: #2 - Teachers are limited to 500 requests per hour."""
        assert RATE_LIMITS[UserRole.TEACHER] == "500/hour"

    def test_student_limit_is_100_per_hour(self) -> None:
        """AC: #3 - Students are limited to 100 requests per hour."""
        assert RATE_LIMITS[UserRole.STUDENT] == "100/hour"

    def test_admin_has_unlimited_access(self) -> None:
        """AC: #4 - Admin has unlimited API access."""
        assert RATE_LIMITS[UserRole.ADMIN] is None

    def test_supervisor_has_unlimited_access(self) -> None:
        """AC: #4 - Supervisor has unlimited API access."""
        assert RATE_LIMITS[UserRole.SUPERVISOR] is None


class TestGetRateLimitKey:
    """Test rate limit key generation (AC: #5, #10)."""

    def test_authenticated_publisher_gets_user_role_key(self) -> None:
        """AC: #5 - Token bucket algorithm per user_id + role combination."""
        user_id = str(uuid4())
        request = create_mock_request(user_id=user_id, role=UserRole.PUBLISHER.value)

        key = get_rate_limit_key(request)

        assert user_id in key
        assert UserRole.PUBLISHER.value in key

    def test_authenticated_teacher_gets_user_role_key(self) -> None:
        """AC: #5 - Teachers get unique rate limit key."""
        user_id = str(uuid4())
        request = create_mock_request(user_id=user_id, role=UserRole.TEACHER.value)

        key = get_rate_limit_key(request)

        assert user_id in key
        assert UserRole.TEACHER.value in key

    def test_authenticated_student_gets_user_role_key(self) -> None:
        """AC: #5 - Students get unique rate limit key."""
        user_id = str(uuid4())
        request = create_mock_request(user_id=user_id, role=UserRole.STUDENT.value)

        key = get_rate_limit_key(request)

        assert user_id in key
        assert UserRole.STUDENT.value in key

    def test_unauthenticated_gets_ip_key(self) -> None:
        """AC: #10 - Unauthenticated requests use IP-based rate limiting."""
        request = create_mock_request(headers={"X-Forwarded-For": "192.168.1.100"})

        key = get_rate_limit_key(request)

        assert key == "192.168.1.100"

    def test_unauthenticated_without_forwarded_header(self) -> None:
        """AC: #10 - Fallback to remote address when no X-Forwarded-For."""
        request = create_mock_request()
        # Mock get_remote_address
        with patch(
            "app.middleware.rate_limit.get_remote_address", return_value="10.0.0.1"
        ):
            key = get_rate_limit_key(request)

        assert key == "10.0.0.1"

    def test_different_users_get_different_keys(self) -> None:
        """AC: #5 - Different users have isolated rate limit buckets."""
        user1_id = str(uuid4())
        user2_id = str(uuid4())

        request1 = create_mock_request(user_id=user1_id, role=UserRole.TEACHER.value)
        request2 = create_mock_request(user_id=user2_id, role=UserRole.TEACHER.value)

        key1 = get_rate_limit_key(request1)
        key2 = get_rate_limit_key(request2)

        assert key1 != key2

    def test_same_user_different_roles_get_different_keys(self) -> None:
        """Edge case: Same user with different roles (if role changes)."""
        user_id = str(uuid4())

        request1 = create_mock_request(user_id=user_id, role=UserRole.TEACHER.value)
        request2 = create_mock_request(user_id=user_id, role=UserRole.PUBLISHER.value)

        key1 = get_rate_limit_key(request1)
        key2 = get_rate_limit_key(request2)

        assert key1 != key2


class TestGetRateLimitForRequest:
    """Test dynamic rate limit resolution based on role (AC: #1-#4)."""

    def test_publisher_gets_1000_per_hour(self) -> None:
        """AC: #1 - Publisher rate limit."""
        request = create_mock_request(
            user_id=str(uuid4()), role=UserRole.PUBLISHER.value
        )

        limit = get_rate_limit_for_request(request)

        assert limit == "1000/hour"

    def test_school_gets_1000_per_hour(self) -> None:
        """School role has same limit as publisher."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.SCHOOL.value)

        limit = get_rate_limit_for_request(request)

        assert limit == "1000/hour"

    def test_teacher_gets_500_per_hour(self) -> None:
        """AC: #2 - Teacher rate limit."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.TEACHER.value)

        limit = get_rate_limit_for_request(request)

        assert limit == "500/hour"

    def test_student_gets_100_per_hour(self) -> None:
        """AC: #3 - Student rate limit."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.STUDENT.value)

        limit = get_rate_limit_for_request(request)

        assert limit == "100/hour"

    def test_admin_gets_unlimited(self) -> None:
        """AC: #4 - Admin has unlimited access."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.ADMIN.value)

        limit = get_rate_limit_for_request(request)

        assert limit is None

    def test_supervisor_gets_unlimited(self) -> None:
        """AC: #4 - Supervisor has unlimited access."""
        request = create_mock_request(
            user_id=str(uuid4()), role=UserRole.SUPERVISOR.value
        )

        limit = get_rate_limit_for_request(request)

        assert limit is None

    def test_unauthenticated_gets_default_limit(self) -> None:
        """AC: #10 - Unauthenticated requests get default IP-based limit."""
        request = create_mock_request()

        limit = get_rate_limit_for_request(request)

        # Default limit for unauthenticated requests
        assert limit == "100/hour"


class TestGetClientIp:
    """Test client IP extraction (AC: #10)."""

    def test_extracts_ip_from_x_forwarded_for(self) -> None:
        """Extract first IP from X-Forwarded-For header (Traefik setup)."""
        request = create_mock_request(headers={"X-Forwarded-For": "203.0.113.1"})

        ip = get_client_ip(request)

        assert ip == "203.0.113.1"

    def test_extracts_first_ip_from_multiple(self) -> None:
        """Handle multiple IPs in X-Forwarded-For (proxy chain)."""
        request = create_mock_request(
            headers={"X-Forwarded-For": "203.0.113.1, 10.0.0.1, 192.168.1.1"}
        )

        ip = get_client_ip(request)

        assert ip == "203.0.113.1"

    def test_strips_whitespace(self) -> None:
        """Handle whitespace in X-Forwarded-For header."""
        request = create_mock_request(headers={"X-Forwarded-For": "  203.0.113.1  "})

        ip = get_client_ip(request)

        assert ip == "203.0.113.1"

    def test_falls_back_to_remote_address(self) -> None:
        """Fallback to remote address when no X-Forwarded-For."""
        request = create_mock_request()

        with patch(
            "app.middleware.rate_limit.get_remote_address", return_value="127.0.0.1"
        ):
            ip = get_client_ip(request)

        assert ip == "127.0.0.1"


class TestRateLimitExceededHandler:
    """Test rate limit exceeded error handling (AC: #7, #8, #9)."""

    @pytest.fixture
    def rate_limit_exception(self) -> MagicMock:
        """Create a mock rate limit exceeded exception."""
        exc = MagicMock(spec=RateLimitExceeded)
        exc.detail = "Rate limit exceeded: 100 per 1 hour"
        exc.retry_after = 3600  # slowapi sets this
        return exc

    @pytest.mark.asyncio
    async def test_returns_429_status_code(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """AC: #7 - Return 429 Too Many Requests."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.STUDENT.value)

        response = await rate_limit_exceeded_handler(request, rate_limit_exception)

        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_returns_rate_limit_exceeded_error_code(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """AC: #7 - Response includes error_code 'RATE_LIMIT_EXCEEDED'."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.STUDENT.value)

        response = await rate_limit_exceeded_handler(request, rate_limit_exception)

        import json

        body = json.loads(response.body.decode())
        assert body["error_code"] == "RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_includes_retry_after_header(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """AC: #8 - Response includes Retry-After header."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.STUDENT.value)

        response = await rate_limit_exceeded_handler(request, rate_limit_exception)

        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "3600"

    @pytest.mark.asyncio
    async def test_includes_request_id(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """Response includes request_id for debugging."""
        request_id = str(uuid4())
        request = create_mock_request(
            user_id=str(uuid4()), role=UserRole.STUDENT.value, request_id=request_id
        )

        response = await rate_limit_exceeded_handler(request, rate_limit_exception)

        import json

        body = json.loads(response.body.decode())
        assert body["request_id"] == request_id

    @pytest.mark.asyncio
    async def test_includes_timestamp(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """Response includes timestamp."""
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.STUDENT.value)

        response = await rate_limit_exceeded_handler(request, rate_limit_exception)

        import json

        body = json.loads(response.body.decode())
        assert "timestamp" in body
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(body["timestamp"].replace("Z", "+00:00"))

    @pytest.mark.asyncio
    async def test_includes_user_details_when_authenticated(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """Response includes user_id and role for authenticated users."""
        user_id = str(uuid4())
        request = create_mock_request(user_id=user_id, role=UserRole.STUDENT.value)

        response = await rate_limit_exceeded_handler(request, rate_limit_exception)

        import json

        body = json.loads(response.body.decode())
        assert body["details"]["user_id"] == user_id
        assert body["details"]["role"] == UserRole.STUDENT.value

    @pytest.mark.asyncio
    async def test_handles_unauthenticated_request(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """Response handles unauthenticated requests gracefully."""
        request = create_mock_request()

        response = await rate_limit_exceeded_handler(request, rate_limit_exception)

        import json

        body = json.loads(response.body.decode())
        assert response.status_code == 429
        assert body["details"]["user_id"] is None
        assert body["details"]["role"] is None

    @pytest.mark.asyncio
    async def test_logs_rate_limit_violation(
        self, rate_limit_exception: RateLimitExceeded
    ) -> None:
        """AC: #9 - Violation is logged for abuse detection."""
        user_id = str(uuid4())
        request = create_mock_request(
            user_id=user_id,
            role=UserRole.STUDENT.value,
            path="/api/v1/assets",
            method="GET",
        )

        with patch("app.middleware.rate_limit.logger") as mock_logger:
            await rate_limit_exceeded_handler(request, rate_limit_exception)

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "Rate limit exceeded"
            extra = call_args[1]["extra"]
            assert extra["user_id"] == user_id
            assert extra["role"] == UserRole.STUDENT.value
            assert extra["endpoint"] == "/api/v1/assets"
            assert extra["method"] == "GET"

    @pytest.mark.asyncio
    async def test_default_retry_after_when_not_set(self) -> None:
        """Fallback to 60 seconds when retry_after not set."""
        exc = MagicMock(spec=RateLimitExceeded)
        exc.detail = "Rate limit exceeded"
        # Don't set retry_after - let spec handle it (returns MagicMock, not int)
        del exc.retry_after  # Remove attribute to test fallback
        request = create_mock_request(user_id=str(uuid4()), role=UserRole.STUDENT.value)

        response = await rate_limit_exceeded_handler(request, exc)

        assert response.headers["Retry-After"] == "60"
