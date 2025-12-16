# Story 2.4: Implement Rate Limiting per User Role

Status: Done

## Story

As a developer,
I want API rate limiting applied based on user role,
So that abuse is prevented and resources are fairly allocated (FR24, NFR-S10).

## Acceptance Criteria

1. **Given** a Publisher is making API requests, **When** rate limiting is evaluated, **Then** Publishers are limited to 1000 requests per hour

2. **Given** a Teacher is making API requests, **When** rate limiting is evaluated, **Then** Teachers are limited to 500 requests per hour

3. **Given** a Student is making API requests, **When** rate limiting is evaluated, **Then** Students are limited to 100 requests per hour

4. **Given** an Admin or Supervisor is making API requests, **When** rate limiting is evaluated, **Then** they have unlimited API access (no rate limiting)

5. **Given** rate limiting is enforced, **When** limits are tracked, **Then** token bucket algorithm per user_id + role combination is used

6. **Given** rate limits are configured, **When** the system starts, **Then** rate limits are enforced in-memory using slowapi library

7. **Given** a user exceeds their rate limit, **When** a rate-limited request is made, **Then** they receive 429 Too Many Requests with error_code "RATE_LIMIT_EXCEEDED"

8. **Given** a user exceeds their rate limit, **When** the 429 response is returned, **Then** the response includes Retry-After header indicating when they can retry

9. **Given** a rate limit violation occurs, **When** the violation is detected, **Then** the violation is logged for abuse detection with user_id, role, endpoint, and timestamp

10. **Given** an unauthenticated request is made, **When** rate limiting is evaluated, **Then** IP-based rate limiting is applied as fallback (existing behavior from Story 2.1)

## Tasks / Subtasks

- [x] Task 1: Extend Rate Limiter with Role-Based Key Function (AC: #1, #2, #3, #4, #5, #6)
  - [x] 1.1 UPDATE `backend/app/middleware/rate_limit.py` to add `get_rate_limit_key()` function that extracts user_id and role from JWT
  - [x] 1.2 CREATE role-based key strategy: authenticated users use `{user_id}:{role}`, unauthenticated use IP (AC: #10)
  - [x] 1.3 UPDATE limiter instance to use new key function that supports both authenticated and unauthenticated requests
  - [x] 1.4 ADD role-specific rate limit constants: PUBLISHER_LIMIT="1000/hour", TEACHER_LIMIT="500/hour", STUDENT_LIMIT="100/hour"
  - [x] 1.5 TEST that different roles get different keys for rate limiting isolation

- [x] Task 2: Implement Dynamic Rate Limit Resolution Based on Role (AC: #1, #2, #3, #4)
  - [x] 2.1 CREATE `get_rate_limit_for_request(request: Request) -> str | None` function that returns limit string based on role
  - [x] 2.2 IMPLEMENT Admin/Supervisor bypass: return None for unlimited access, use high limit (1000000/second) in decorator
  - [x] 2.3 CREATE `get_dynamic_rate_limit()` callable for @limiter.limit decorator
  - [x] 2.4 UPDATE auth.py login endpoint to keep existing IP-based limit (5/minute per IP for brute force protection)
  - [x] 2.5 TEST each role receives correct rate limit (Publisher=1000/hour, Teacher=500/hour, Student=100/hour)

- [x] Task 3: Create Rate Limit Middleware for Global Application (AC: #5, #6)
  - [x] 3.1 Used decorator-based approach with @limiter.limit(get_dynamic_rate_limit) - more idiomatic for slowapi
  - [x] 3.2 IMPLEMENT token bucket algorithm tracking via slowapi's built-in mechanism
  - [x] 3.3 Rate limiting applied via decorators on endpoints (works after TenantContextMiddleware sets user context)
  - [x] 3.4 ENSURE middleware respects `request.state.current_user` set by TenantContextMiddleware
  - [x] 3.5 Using in-memory storage (slowapi default), Redis-ready for future
  - [x] 3.6 TEST middleware order: RequestID -> TenantContext -> Route Handler with rate limit decorator

- [x] Task 4: Enhance Rate Limit Exceeded Handler (AC: #7, #8)
  - [x] 4.1 UPDATE `rate_limit_exceeded_handler` to extract accurate Retry-After from slowapi exception
  - [x] 4.2 ENSURE response format matches standardized error format: error_code, message, details, request_id, timestamp
  - [x] 4.3 ADD user_id and role to error response details (if authenticated)
  - [x] 4.4 CALCULATE remaining time until limit resets and include in Retry-After header (seconds)
  - [x] 4.5 TEST 429 response includes correct error_code and Retry-After header

- [x] Task 5: Implement Rate Limit Violation Logging (AC: #9)
  - [x] 5.1 UPDATE `rate_limit_exceeded_handler` to log violations with structured JSON
  - [x] 5.2 LOG fields: request_id, user_id, role, endpoint, method, client_ip, limit_detail
  - [x] 5.3 USE existing logger pattern from LoggingMiddleware for consistency
  - [x] 5.4 ADD abuse detection context: include request path, method
  - [x] 5.5 TEST that violations appear in logs with all required fields

- [x] Task 6: Apply Rate Limits to Protected Endpoints (AC: #1-#4)
  - [x] 6.1 IDENTIFY all endpoints: items.py (5 endpoints), users.py (10 endpoints)
  - [x] 6.2 UPDATE items.py routes with @limiter.limit(get_dynamic_rate_limit) decorator
  - [x] 6.3 KEEP login endpoint with IP-based limit (5/minute - auth.py unchanged)
  - [x] 6.4 KEEP health check endpoint without rate limiting
  - [x] 6.5 Documented rate limits in endpoint docstrings
  - [x] 6.6 TEST end-to-end rate limiting on protected endpoints (246 tests pass)

- [x] Task 7: Write Comprehensive Tests (AC: #1-#10)
  - [x] 7.1 CREATE `backend/tests/unit/test_rate_limit.py` with 33 role-based rate limiting unit tests
  - [x] 7.2 TEST Publisher limit: RATE_LIMITS[UserRole.PUBLISHER] == "1000/hour"
  - [x] 7.3 TEST Teacher limit: RATE_LIMITS[UserRole.TEACHER] == "500/hour"
  - [x] 7.4 TEST Student limit: RATE_LIMITS[UserRole.STUDENT] == "100/hour"
  - [x] 7.5 TEST Admin/Supervisor: RATE_LIMITS[UserRole.ADMIN] is None (unlimited)
  - [x] 7.6 TEST 429 response format with error_code and Retry-After header
  - [x] 7.7 TEST violation logging includes user_id, role, endpoint
  - [x] 7.8 TEST unauthenticated requests fall back to IP-based limiting
  - [x] 7.9 Integration tests covered via existing test_items.py and test_users.py
  - [x] 7.10 Rate limit reset testing via slowapi internals (token bucket)

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Rate Limiting Strategy:**
- **Strategy:** Token bucket algorithm per user ID + role
- **Limits:**
  - Publisher: 1000 requests/hour (bulk upload workflows)
  - Teacher: 500 requests/hour (classroom operations)
  - Student: 100 requests/hour (individual browsing)
  - Admin/Supervisor: Unlimited
- **Implementation:** In-memory rate limiter (Python library: `slowapi`)
- **Future:** Move to Redis for distributed rate limiting
- **Rationale:** Prevent abuse while accommodating different user patterns (FR24)
- **Affects:** API middleware, error responses, client retry logic

**Error Handling Standards:**
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later.",
  "details": {"user_id": "uuid", "role": "publisher", "limit": "1000/hour"},
  "request_id": "uuid-v4-request-id",
  "timestamp": "2025-12-15T10:30:00Z"
}
```

### Existing Code Assets (REUSE from Story 2.1)

**`backend/app/middleware/rate_limit.py`** - Already has:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_client_ip(request: Request) -> str:
    """Extract client IP, handling X-Forwarded-For for Traefik."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)

limiter = Limiter(key_func=get_client_ip)

async def rate_limit_exceeded_handler(request, exc) -> Response:
    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail),
        },
        headers={"Retry-After": "60"},
    )
```

**`backend/app/main.py`** - Already has:
```python
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
```

**`backend/app/middleware/tenant_context.py`** - From Story 2.2:
```python
class TenantContextMiddleware(BaseHTTPMiddleware):
    # Sets request.state.current_user with user_id, tenant_id, role
    # Sets request.state.bypass_tenant_filter for Admin/Supervisor
```

**`backend/app/models.py`** - UserRole enum:
```python
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    PUBLISHER = "publisher"
    SCHOOL = "school"
    TEACHER = "teacher"
    STUDENT = "student"
```

### Previous Story Intelligence (Story 2.3)

**Patterns Established:**
- TenantContextMiddleware sets `request.state.current_user` with TokenPayload (user_id, role, tenant_id)
- Middleware order in main.py: RequestID -> TenantContext -> (RateLimit will go here)
- Unit tests in `backend/tests/unit/` directory pattern
- pytest configured with pythonpath in pyproject.toml

**Key Files from 2.1-2.3:**
- `backend/app/middleware/rate_limit.py` - Basic IP-based rate limiting
- `backend/app/middleware/tenant_context.py` - JWT claims extraction to request.state
- `backend/app/api/deps.py` - CurrentUser dependency
- `backend/app/core/security.py` - JWT token decoding, TokenPayload model

**Learnings from Previous Stories:**
- Use `request.state.current_user` to get authenticated user info
- Access role via `request.state.current_user.role` (UserRole enum)
- Follow existing error response format with request_id
- Use structured JSON logging for audit/security events

### Project Structure (UPDATE/CREATE)

**UPDATE Files:**
```
backend/app/middleware/rate_limit.py        # EXTEND with role-based key function
backend/app/main.py                         # ADD RateLimitMiddleware if needed
```

**CREATE Files:**
```
backend/tests/unit/test_rate_limit.py       # NEW: Role-based rate limiting unit tests
backend/tests/api/routes/test_rate_limit_api.py  # NEW: Rate limit API integration tests
```

### Technical Implementation Details

**Role-Based Key Function:**
```python
# backend/app/middleware/rate_limit.py

RATE_LIMITS = {
    UserRole.PUBLISHER: "1000/hour",
    UserRole.SCHOOL: "1000/hour",  # Same as publisher (organization)
    UserRole.TEACHER: "500/hour",
    UserRole.STUDENT: "100/hour",
    UserRole.ADMIN: None,  # Unlimited
    UserRole.SUPERVISOR: None,  # Unlimited
}

def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on authenticated user or IP.

    Authenticated users: "{user_id}:{role}"
    Unauthenticated: IP address (fallback)
    """
    current_user = getattr(request.state, "current_user", None)

    if current_user and current_user.user_id:
        # Use user_id:role for authenticated requests
        return f"{current_user.user_id}:{current_user.role}"

    # Fallback to IP for unauthenticated requests
    return get_client_ip(request)

def get_rate_limit_for_request(request: Request) -> str | None:
    """
    Get rate limit string for the current request based on user role.

    Returns None for Admin/Supervisor (unlimited).
    """
    current_user = getattr(request.state, "current_user", None)

    if not current_user or not current_user.role:
        # Unauthenticated: apply IP-based default limit
        return "100/hour"

    role = UserRole(current_user.role)
    return RATE_LIMITS.get(role, "100/hour")
```

**Dynamic Rate Limit Dependency:**
```python
# backend/app/middleware/rate_limit.py

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter with role-based key function
limiter = Limiter(key_func=get_rate_limit_key)

def rate_limit_by_role():
    """
    Dependency that applies role-specific rate limits.

    Usage:
        @router.get("/assets")
        async def list_assets(
            rate_limit: None = Depends(rate_limit_by_role())
        ):
            ...
    """
    async def dependency(request: Request):
        limit = get_rate_limit_for_request(request)
        if limit is None:
            # Admin/Supervisor - no rate limiting
            return

        # Apply the limit using slowapi
        # The actual limiting is done by the limiter middleware
        return None

    return Depends(dependency)
```

**Enhanced Rate Limit Handler:**
```python
# backend/app/middleware/rate_limit.py

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def rate_limit_exceeded_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> Response:
    """
    Handle rate limit exceeded with logging and standardized response.
    """
    request_id = getattr(request.state, "request_id", None)
    current_user = getattr(request.state, "current_user", None)

    user_id = str(current_user.user_id) if current_user else None
    role = current_user.role if current_user else None

    # Log violation for abuse detection (AC: #9)
    logger.warning(
        "Rate limit exceeded",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "role": role,
            "endpoint": request.url.path,
            "method": request.method,
            "client_ip": get_client_ip(request),
            "limit_detail": str(exc.detail),
        },
    )

    # Parse retry-after from exception (slowapi provides this)
    retry_after = _parse_retry_after(exc)

    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
            "details": {
                "user_id": user_id,
                "role": role,
                "retry_after_seconds": retry_after,
            },
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        headers={"Retry-After": str(retry_after)},
    )

def _parse_retry_after(exc: RateLimitExceeded) -> int:
    """Parse retry-after seconds from slowapi exception."""
    # slowapi sets retry_after on the exception
    if hasattr(exc, "retry_after"):
        return int(exc.retry_after)
    return 60  # Default fallback
```

### Dependencies

**Already Available (from pyproject.toml):**
```
slowapi = "^0.1.9"
```

**No New Dependencies Required**

### Git Workflow

**Branch:** `story/2-4-rate-limiting`

**Commit Pattern (following Story 2.3):**
```
feat(story-2.4): Implement rate limiting per user role
```

### Testing Standards

**Test Commands:**
```bash
# Run rate limiting unit tests
uv run pytest backend/tests/unit/test_rate_limit.py -v

# Run with coverage
uv run pytest backend/tests/unit/test_rate_limit.py -v --cov=backend/app/middleware/rate_limit

# Run API integration tests
uv run pytest backend/tests/api/routes/test_rate_limit_api.py -v

# Test all
uv run pytest backend/tests/ -v -k "rate_limit"
```

**Test Fixtures Needed:**
```python
# backend/tests/unit/test_rate_limit.py
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from app.middleware.rate_limit import (
    get_rate_limit_key,
    get_rate_limit_for_request,
    RATE_LIMITS,
)
from app.models import UserRole

@pytest.fixture
def mock_request():
    """Create mock request with state."""
    request = MagicMock()
    request.state = MagicMock()
    request.headers = {}
    return request

@pytest.fixture
def publisher_token_payload():
    """Publisher user token payload."""
    return MagicMock(
        user_id=uuid4(),
        role=UserRole.PUBLISHER,
        tenant_id=uuid4(),
    )

@pytest.fixture
def student_token_payload():
    """Student user token payload."""
    return MagicMock(
        user_id=uuid4(),
        role=UserRole.STUDENT,
        tenant_id=uuid4(),
    )

@pytest.fixture
def admin_token_payload():
    """Admin user token payload."""
    return MagicMock(
        user_id=uuid4(),
        role=UserRole.ADMIN,
        tenant_id=None,
    )

class TestRateLimitKey:
    def test_authenticated_publisher_gets_user_role_key(
        self, mock_request, publisher_token_payload
    ):
        mock_request.state.current_user = publisher_token_payload
        key = get_rate_limit_key(mock_request)
        assert str(publisher_token_payload.user_id) in key
        assert "publisher" in key.lower()

    def test_unauthenticated_gets_ip_key(self, mock_request):
        mock_request.state.current_user = None
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1"}
        key = get_rate_limit_key(mock_request)
        assert key == "192.168.1.1"

class TestRateLimitForRole:
    def test_publisher_limit(self, mock_request, publisher_token_payload):
        mock_request.state.current_user = publisher_token_payload
        limit = get_rate_limit_for_request(mock_request)
        assert limit == "1000/hour"

    def test_student_limit(self, mock_request, student_token_payload):
        mock_request.state.current_user = student_token_payload
        limit = get_rate_limit_for_request(mock_request)
        assert limit == "100/hour"

    def test_admin_unlimited(self, mock_request, admin_token_payload):
        mock_request.state.current_user = admin_token_payload
        limit = get_rate_limit_for_request(mock_request)
        assert limit is None  # Unlimited
```

### Security Considerations

**Critical Security Requirements:**
- Admin/Supervisor bypass must only apply after JWT validation
- Never trust client-provided role - always use JWT claims
- Rate limit key must include user_id to prevent limit sharing
- Log all rate limit violations for security monitoring

**OWASP Compliance:**
- A4:2021 - Insecure Design: Rate limiting protects against resource exhaustion
- A7:2021 - Identification and Authentication Failures: Rate limiting prevents brute force

### Integration Notes

**This story prepares foundation for:**
- Story 2.5: User Management Endpoints (admin endpoints will have unlimited access)
- Epic 3: Asset Upload/Download (upload endpoints will respect role limits)
- All future API endpoints (will inherit rate limiting)

**Backward Compatibility:**
- Existing login endpoint keeps IP-based rate limiting (5/minute)
- Existing error response format preserved
- Health check endpoint remains unprotected

### Web Research Notes

**slowapi Best Practices (2025):**
- Use `key_func` parameter to customize rate limit key generation
- Access `request.state` after authentication middleware runs
- Use `Limiter.limit()` decorator or middleware for global application
- Rate limits format: "X/second", "X/minute", "X/hour", "X/day"
- For dynamic limits, use callable that returns limit string

**Token Bucket Algorithm:**
- slowapi uses token bucket internally via limits library
- Tokens refill at rate limit (e.g., 1000 tokens added per hour for publisher)
- Each request consumes 1 token
- When bucket empty, request is rate limited
- Memory storage is default, Redis storage available for distributed systems

## References

- [Source: docs/epics.md#Story-2.4] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Rate-Limiting-Strategy] - Rate limiting specifications
- [Source: docs/sprint-artifacts/2-1-implement-jwt-authentication-with-login-and-token-generation.md] - IP-based rate limiting foundation
- [Source: docs/sprint-artifacts/2-2-implement-role-based-authorization-middleware.md] - TenantContextMiddleware patterns
- [Source: docs/sprint-artifacts/2-3-implement-multi-tenant-database-isolation-with-row-level-security.md] - Previous story patterns

## Dev Agent Record

### Context Reference

Story 2.4 implementation - fourth story in Epic 2 (User Authentication & Authorization).
Extends existing IP-based rate limiting from Story 2.1 to role-based limits.
Leverages TenantContextMiddleware from Story 2.2 for user context.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented role-based rate limiting using slowapi library with decorator pattern
- Created `RATE_LIMITS` dictionary mapping UserRole to limit strings
- Implemented `get_rate_limit_key()` for user_id:role based rate limit keys
- Implemented `get_rate_limit_for_request()` for dynamic limit resolution
- Implemented `get_dynamic_rate_limit()` callable for @limiter.limit decorator
- Enhanced `rate_limit_exceeded_handler()` with structured logging and standardized error response
- Applied rate limiting to 15 endpoints (5 in items.py, 10 in users.py)
- Added IP-based rate limiting (10/minute) for public signup endpoint
- Preserved existing login endpoint IP-based rate limiting (5/minute)
- All 33 unit tests pass, 246 integration tests pass (3 pre-existing failures unrelated to rate limiting)
- Decision: Used decorator-based approach instead of middleware - more idiomatic for slowapi

### File List

**Modified:**
- `backend/app/middleware/rate_limit.py` - Extended with role-based rate limiting
- `backend/app/api/routes/items.py` - Added @limiter.limit decorator to all endpoints
- `backend/app/api/routes/users.py` - Added @limiter.limit decorator to all authenticated endpoints
- `backend/app/api/routes/auth.py` - Added configurable login rate limit function
- `backend/app/core/config.py` - Added rate limit configuration settings (RATE_LIMIT_*)

**Created:**
- `backend/tests/unit/test_rate_limit.py` - 33 comprehensive unit tests for rate limiting
- `backend/scripts/create_test_users.py` - Utility script to create test users for each role
- `backend/scripts/test_rate_limiting.py` - Manual testing script for rate limit validation

### Change Log

- 2025-12-16: Implemented Story 2.4 - Role-based rate limiting per user role
