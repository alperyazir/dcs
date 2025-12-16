# Story 2.2: Implement Role-Based Authorization Middleware

Status: Ready for Review

## Story

As a developer,
I want role-based authorization enforced on all API endpoints,
So that users can only access resources based on their role (FR22, NFR-S3).

## Acceptance Criteria

1. **Given** a user is authenticated with a valid JWT, **When** they access an API endpoint, **Then** the authorization middleware extracts role and tenant_id from the JWT

2. **Given** an Admin or Supervisor user, **When** they access any tenant's resources, **Then** they are granted access (bypass tenant filtering) (FR13, FR14)

3. **Given** a Publisher user, **When** they attempt to write operations, **Then** they can only write to `/publishers/{their_id}/` storage (FR15)

4. **Given** a School user, **When** they attempt to write operations, **Then** they can only write to `/schools/{their_id}/` storage (FR16)

5. **Given** a Teacher user, **When** they attempt to write operations, **Then** they can only write to `/teachers/{their_id}/` storage (FR17)

6. **Given** a Student user, **When** they attempt to write operations, **Then** they can only write to `/students/{their_id}/` storage (FR18)

7. **Given** a user attempts to access a resource they're not authorized for, **When** the authorization check fails, **Then** they receive 403 Forbidden with error_code "PERMISSION_DENIED"

8. **Given** any authorization denial, **When** the denial occurs, **Then** the attempt is logged in audit logs with user_id, action, resource, and timestamp

9. **Given** protected endpoints with role requirements, **When** accessed by users without required role, **Then** return 403 with descriptive error message

10. **Given** a dependency injection system, **When** routes need role-based protection, **Then** reusable dependencies like `require_admin`, `require_publisher_or_above` are available

## Tasks / Subtasks

- [x] Task 1: Extend User Model with Role Enum and Tenant Association (AC: #1, #2, #3-#6)
  - [x] 1.1 VERIFY `backend/app/models.py` has `UserRole` enum with values: admin, supervisor, publisher, school, teacher, student
  - [x] 1.2 VERIFY User model includes `role: UserRole` and `tenant_id: UUID` fields
  - [x] 1.3 CREATE role hierarchy constant: `ROLE_HIERARCHY = {"admin": 6, "supervisor": 5, "publisher": 4, "school": 3, "teacher": 2, "student": 1}`
  - [x] 1.4 ADD helper function `has_role_or_higher(user_role: UserRole, required_role: UserRole) -> bool`

- [x] Task 2: CREATE Authorization Dependency Functions (AC: #1, #2, #9, #10)
  - [x] 2.1 CREATE `backend/app/api/deps_auth.py` for authorization dependencies
  - [x] 2.2 Implement `require_authenticated` - base dependency ensuring valid JWT (reuses existing get_current_user)
  - [x] 2.3 Implement `require_admin` - only Admin role
  - [x] 2.4 Implement `require_supervisor_or_above` - Admin or Supervisor
  - [x] 2.5 Implement `require_role(required_role: UserRole)` - factory function for specific role
  - [x] 2.6 Implement `require_role_or_above(minimum_role: UserRole)` - factory using role hierarchy
  - [x] 2.7 All auth failures return 403 with `{"error_code": "PERMISSION_DENIED", "message": "...", "details": {...}}`

- [x] Task 3: CREATE Resource Ownership Validation (AC: #3, #4, #5, #6)
  - [x] 3.1 CREATE `backend/app/services/authorization_service.py` with `AuthorizationService` class
  - [x] 3.2 Implement `validate_resource_ownership(user: User, resource_owner_id: UUID, resource_owner_type: str) -> bool`
  - [x] 3.3 Define owner type to role mapping: `{"publishers": "publisher", "schools": "school", "teachers": "teacher", "students": "student"}`
  - [x] 3.4 Admin/Supervisor always return True (full access)
  - [x] 3.5 Other roles: user.role must match owner_type AND user.id must match owner_id
  - [x] 3.6 Implement `get_allowed_storage_prefix(user: User) -> str` returning path like `/publishers/{user.id}/`

- [x] Task 4: CREATE Tenant Context Middleware (AC: #1, #2)
  - [x] 4.1 CREATE `backend/app/middleware/tenant_context.py`
  - [x] 4.2 Implement middleware that extracts `tenant_id` from JWT and injects into `request.state.tenant_id`
  - [x] 4.3 Implement middleware that extracts full user context: `request.state.user_id`, `request.state.role`, `request.state.tenant_id`
  - [x] 4.4 For Admin/Supervisor: Set `request.state.bypass_tenant_filter = True`
  - [x] 4.5 Register middleware in `backend/app/main.py`

- [x] Task 5: CREATE Permission Denied Exception Handler (AC: #7, #8)
  - [x] 5.1 UPDATE `backend/app/core/exceptions.py` - ADD `PermissionDeniedException` class
  - [x] 5.2 Exception should accept: `user_id`, `resource_type`, `resource_id`, `action`, `reason`
  - [x] 5.3 Format as: `{"error_code": "PERMISSION_DENIED", "message": "...", "details": {...}, "request_id": "...", "timestamp": "..."}`
  - [x] 5.4 Register exception handler in `backend/app/main.py` to return 403 status
  - [x] 5.5 Ensure exception handler logs attempt with request_id for audit trail

- [x] Task 6: CREATE Authorization Audit Logging (AC: #8)
  - [x] 6.1 UPDATE `backend/app/services/audit_service.py` or CREATE if not exists
  - [x] 6.2 Implement `log_authorization_denial(user_id: UUID, action: str, resource_type: str, resource_id: UUID, reason: str)`
  - [x] 6.3 Log entry includes: user_id, action, resource_type, resource_id, ip_address, timestamp, request_id, reason
  - [x] 6.4 Use existing structured logging from Story 1.5 (JSON format with request_id)
  - [x] 6.5 Integrate with PermissionDeniedException to auto-log denials

- [x] Task 7: UPDATE Existing Routes with Authorization (AC: #1-#10)
  - [x] 7.1 UPDATE `backend/app/api/routes/users.py` - Add `require_admin` dependency for user management
  - [x] 7.2 UPDATE `backend/app/api/routes/login.py` - No changes (public endpoint)
  - [x] 7.3 UPDATE `backend/app/api/routes/auth.py` - No changes (already uses get_current_user)
  - [x] 7.4 UPDATE `backend/app/api/deps.py` - Export new authorization dependencies
  - [x] 7.5 UPDATE `backend/app/api/main.py` - Ensure middleware order is correct (tenant context before routes)

- [x] Task 8: CREATE MinIO Path Validation Integration (AC: #3, #4, #5, #6)
  - [x] 8.1 UPDATE `backend/app/services/minio_service.py` (or prepare for future)
  - [x] 8.2 ADD method `validate_path_access(user: User, object_path: str) -> bool`
  - [x] 8.3 Parse object_path to extract owner_type and owner_id (e.g., `/publishers/123/file.pdf`)
  - [x] 8.4 Use AuthorizationService.validate_resource_ownership for validation
  - [x] 8.5 Raise PermissionDeniedException if access denied

- [x] Task 9: Write Comprehensive Tests (AC: #1-#10)
  - [x] 9.1 CREATE `backend/tests/unit/test_authorization.py` (moved to unit tests for fast execution)
  - [x] 9.2 Test Admin can access all resources across tenants
  - [x] 9.3 Test Supervisor can access all resources across tenants
  - [x] 9.4 Test Publisher can only write to own storage prefix
  - [x] 9.5 Test Teacher can only write to own storage prefix
  - [x] 9.6 Test Student can only write to own storage prefix
  - [x] 9.7 Test 403 returned when accessing unauthorized resource
  - [x] 9.8 Test audit log created on authorization denial
  - [x] 9.9 Test require_admin dependency blocks non-admin users
  - [x] 9.10 Test role hierarchy helper functions
  - [x] 9.11 Test tenant context middleware injects correct values

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Multi-Tenant Authorization Pattern:**
- Role-based access control (RBAC) with row-level security
- PostgreSQL row-level security (RLS) policies on all tenant-specific tables
- Middleware injects `current_user_id` and `tenant_id` into all database queries
- Ownership validation: Users write only to their own prefix (publishers/{id}/, teachers/{id}/, etc.)

**Role Hierarchy (from architecture):**
- **Admin/Supervisor:** Full access to all tenants (bypass RLS)
- **Publisher:** Write to `/publishers/{id}/`, read own assets + granted assets
- **Teacher:** Write to `/teachers/{id}/`, read granted assets from publishers + own creations
- **Student:** Read-only access to assets granted by teacher via LMS
- **School:** Organizational role, manages teacher accounts

**Service Layer Architecture:**
- Routes → Services → Repositories pattern
- Services contain business logic (authorization checks)
- Routes handle HTTP concerns only

### Existing Code Assets (REUSE)

**`backend/app/api/deps.py`** - Already has:
```python
def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """Dependency for authenticated endpoints - validates JWT and returns user."""
    # This is the foundation for all authorization
```

**`backend/app/models.py`** - User model with:
- `id`, `email`, `hashed_password`, `is_active`
- `role: UserRole` enum (likely needs verification/extension)
- `tenant_id: UUID` for multi-tenant isolation

**`backend/app/core/security.py`** - JWT payload includes:
- `sub` (user_id), `email`, `role`, `tenant_id`, `exp`, `iat`

**`backend/app/middleware/rate_limit.py`** - Existing middleware pattern to follow

**`backend/app/core/exceptions.py`** - Custom exception pattern (if exists from Story 2.1)

### Previous Story Intelligence (Story 2.1)

**Patterns Established:**
- JWT token payload includes: sub (user_id), email, role, tenant_id, exp, iat
- Token verification uses RS256 public key
- Claims validation in `deps.py:get_current_user`
- Rate limiting middleware pattern in `middleware/rate_limit.py`
- Structured logging with request_id from middleware
- Custom exceptions with standardized error format

**Key Files Modified in 2.1:**
- `backend/app/core/security.py` - Token creation/verification
- `backend/app/api/deps.py` - get_current_user with claims validation
- `backend/app/middleware/rate_limit.py` - Middleware pattern example

**Learnings from 2.1:**
- Use existing `get_current_user` as foundation
- Claims validation already extracts role and tenant_id from JWT
- Follow same error response format: `{error_code, message, details, request_id, timestamp}`
- Include request_id in all logging for traceability

### Project Structure

**UPDATE Files:**
```
backend/app/models.py                    # VERIFY UserRole enum has all roles
backend/app/api/deps.py                  # ADD export for new auth dependencies
backend/app/core/exceptions.py           # ADD PermissionDeniedException
backend/app/main.py                      # REGISTER tenant context middleware
backend/app/api/routes/users.py          # ADD require_admin dependency
```

**CREATE Files:**
```
backend/app/api/deps_auth.py             # NEW: Authorization dependencies (require_admin, etc.)
backend/app/services/authorization_service.py  # NEW: Resource ownership validation
backend/app/middleware/tenant_context.py # NEW: Tenant context injection
backend/tests/api/routes/test_authorization.py  # NEW: Authorization tests
```

### Technical Implementation Details

**Role Hierarchy Constant:**
```python
# backend/app/core/constants.py or authorization_service.py
from app.models import UserRole

ROLE_HIERARCHY = {
    UserRole.admin: 6,
    UserRole.supervisor: 5,
    UserRole.publisher: 4,
    UserRole.school: 3,
    UserRole.teacher: 2,
    UserRole.student: 1,
}

def has_role_or_higher(user_role: UserRole, required_role: UserRole) -> bool:
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)
```

**Authorization Dependencies:**
```python
# backend/app/api/deps_auth.py
from fastapi import Depends, HTTPException, status
from app.api.deps import get_current_user
from app.models import User, UserRole
from app.core.exceptions import PermissionDeniedException

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise PermissionDeniedException(
            user_id=current_user.id,
            resource_type="admin_endpoint",
            resource_id=None,
            action="access",
            reason=f"Admin role required, user has {current_user.role.value}"
        )
    return current_user

def require_supervisor_or_above(current_user: User = Depends(get_current_user)) -> User:
    if not has_role_or_higher(current_user.role, UserRole.supervisor):
        raise PermissionDeniedException(
            user_id=current_user.id,
            resource_type="supervisor_endpoint",
            resource_id=None,
            action="access",
            reason=f"Supervisor or higher role required"
        )
    return current_user

def require_role(required_role: UserRole):
    """Factory function for specific role requirement."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise PermissionDeniedException(
                user_id=current_user.id,
                resource_type=f"{required_role.value}_endpoint",
                resource_id=None,
                action="access",
                reason=f"{required_role.value} role required"
            )
        return current_user
    return dependency
```

**Authorization Service:**
```python
# backend/app/services/authorization_service.py
from uuid import UUID
from app.models import User, UserRole

OWNER_TYPE_TO_ROLE = {
    "publishers": UserRole.publisher,
    "schools": UserRole.school,
    "teachers": UserRole.teacher,
    "students": UserRole.student,
}

class AuthorizationService:
    @staticmethod
    def validate_resource_ownership(
        user: User,
        resource_owner_id: UUID,
        resource_owner_type: str
    ) -> bool:
        """Check if user can access/modify resource based on ownership."""
        # Admin/Supervisor bypass all ownership checks
        if user.role in [UserRole.admin, UserRole.supervisor]:
            return True

        # Map owner type to expected role
        expected_role = OWNER_TYPE_TO_ROLE.get(resource_owner_type)
        if not expected_role:
            return False

        # User must have matching role AND matching ID
        return user.role == expected_role and user.id == resource_owner_id

    @staticmethod
    def get_allowed_storage_prefix(user: User) -> str:
        """Get the storage path prefix user can write to."""
        role_to_prefix = {
            UserRole.admin: "/",  # Full access
            UserRole.supervisor: "/",  # Full access
            UserRole.publisher: f"/publishers/{user.id}/",
            UserRole.school: f"/schools/{user.id}/",
            UserRole.teacher: f"/teachers/{user.id}/",
            UserRole.student: f"/students/{user.id}/",
        }
        return role_to_prefix.get(user.role, "")

    @staticmethod
    def can_write_to_path(user: User, object_path: str) -> bool:
        """Check if user can write to given object path."""
        if user.role in [UserRole.admin, UserRole.supervisor]:
            return True

        allowed_prefix = AuthorizationService.get_allowed_storage_prefix(user)
        return object_path.startswith(allowed_prefix)
```

**Tenant Context Middleware:**
```python
# backend/app/middleware/tenant_context.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import jwt
from app.core.config import settings
from app.models import UserRole

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_PUBLIC_KEY,
                    algorithms=["RS256"]
                )
                request.state.user_id = payload.get("sub")
                request.state.tenant_id = payload.get("tenant_id")
                request.state.role = payload.get("role")

                # Admin/Supervisor bypass tenant filtering
                if payload.get("role") in ["admin", "supervisor"]:
                    request.state.bypass_tenant_filter = True
                else:
                    request.state.bypass_tenant_filter = False
            except jwt.PyJWTError:
                # Token invalid, let route-level auth handle it
                pass

        response = await call_next(request)
        return response
```

**Permission Denied Exception:**
```python
# backend/app/core/exceptions.py
from uuid import UUID
from typing import Optional
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class PermissionDeniedException(HTTPException):
    def __init__(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: Optional[UUID],
        action: str,
        reason: str
    ):
        detail = {
            "error_code": "PERMISSION_DENIED",
            "message": f"You do not have permission to {action} this {resource_type}",
            "details": {
                "user_id": str(user_id),
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
                "action": action,
                "reason": reason
            }
        }
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

        # Log the denial for audit
        logger.warning(
            f"Authorization denied: user={user_id} action={action} "
            f"resource_type={resource_type} resource_id={resource_id} reason={reason}"
        )
```

### Dependencies

**Already Available:**
- `pyjwt[crypto]` - JWT handling (from Story 2.1)
- `python-multipart` - Form handling
- FastAPI dependency injection system

**No New Dependencies Required**

### Git Workflow

**Branch:** `story/2-2-role-based-authorization`

**Commit Pattern (following Story 2.1):**
```
feat(story-2.2): Implement Role-Based Authorization Middleware
```

### Testing Standards

**Test Commands:**
```bash
# Run authorization tests
uv run pytest backend/tests/api/routes/test_authorization.py -v

# Test admin access
curl -X GET http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# Test forbidden access (student trying admin endpoint)
curl -X GET http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer ${STUDENT_TOKEN}"
# Should return 403 with PERMISSION_DENIED
```

**Test Fixtures Needed:**
```python
# backend/tests/conftest.py - add these fixtures
@pytest.fixture
def admin_user(db_session):
    """Create admin user for testing."""
    return create_test_user(role=UserRole.admin)

@pytest.fixture
def publisher_user(db_session):
    """Create publisher user for testing."""
    return create_test_user(role=UserRole.publisher)

@pytest.fixture
def teacher_user(db_session):
    """Create teacher user for testing."""
    return create_test_user(role=UserRole.teacher)

@pytest.fixture
def student_user(db_session):
    """Create student user for testing."""
    return create_test_user(role=UserRole.student)
```

### Security Considerations

**Critical Security Requirements:**
- Never expose internal authorization logic details in error messages to external users
- Log all authorization denials with sufficient context for security audits
- Ensure Admin/Supervisor bypass is correctly implemented (not granting access to invalid tokens)
- Validate that tenant_id from JWT cannot be spoofed
- Use constant-time comparison for role checks where applicable

**OWASP Compliance:**
- A1:2021 - Broken Access Control: Implement proper RBAC checks on all endpoints
- A4:2021 - Insecure Design: Follow principle of least privilege
- A7:2021 - Identification and Authentication Failures: Build on Story 2.1's secure JWT

### Integration Notes

**This story prepares foundation for:**
- Story 2.3: Multi-Tenant Database Isolation with Row-Level Security (uses tenant context)
- Story 2.4: Rate Limiting per User Role (uses role from context)
- Story 2.5: User Management Endpoints (uses require_admin dependency)
- Story 3.x: Asset Upload/Download (uses path validation)

**Backward Compatibility:**
- All existing endpoints continue to work with existing tokens
- New authorization layer is additive, not breaking
- Existing `get_current_user` dependency unchanged

## References

- [Source: docs/epics.md#Story-2.2] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Authentication-Security] - Authorization specifications
- [Source: docs/architecture/implementation-patterns-consistency-rules.md] - Naming and structure patterns
- [Source: docs/sprint-artifacts/2-1-implement-jwt-authentication-with-login-and-token-generation.md] - Previous story patterns

## Dev Agent Record

### Context Reference

Story 2.2 implementation - second story in Epic 2 (User Authentication & Authorization).
Builds directly on Story 2.1 (JWT Authentication) infrastructure.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Task 1 Complete**: Verified UserRole enum has all 6 roles (ADMIN, SUPERVISOR, PUBLISHER, SCHOOL, TEACHER, STUDENT). Created ROLE_HIERARCHY constant and has_role_or_higher() helper in authorization_service.py.

2. **Task 2 Complete**: Created deps_auth.py with require_authenticated, require_admin, require_supervisor_or_above, require_role(), and require_role_or_above() factory functions. All return 403 with PERMISSION_DENIED error_code.

3. **Task 3 Complete**: Created AuthorizationService class with validate_resource_ownership(), get_allowed_storage_prefix(), and can_write_to_path() methods. Admin/Supervisor bypass implemented.

4. **Task 4 Complete**: Created TenantContextMiddleware that extracts user_id, tenant_id, role from JWT and sets bypass_tenant_filter for Admin/Supervisor. Registered in main.py.

5. **Task 5 Complete**: Created PermissionDeniedException in core/exceptions.py with standardized error format including error_code, message, details, and timestamp. Auto-logs denials.

6. **Task 6 Complete**: Created AuditService with log_authorization_denial() for structured JSON logging of security events.

7. **Task 7 Complete**: Updated users.py routes (read_users, create_user, update_user, delete_user) to include require_admin dependency alongside existing superuser check.

8. **Task 8 Complete**: Added validate_path_access() and parse_path_ownership() to AuthorizationService for MinIO path validation. Raises PermissionDeniedException on access denial.

9. **Task 9 Complete**: Created 38 unit tests in tests/unit/test_authorization.py covering all ACs. All tests passing.

### File List

**VERIFIED Files:**
- `backend/app/models.py` - UserRole enum has all 6 roles ✓

**UPDATED Files:**
- `backend/app/main.py` - Registered TenantContextMiddleware
- `backend/app/api/routes/users.py` - Added require_admin dependency to admin endpoints

**CREATED Files:**
- `backend/app/api/deps_auth.py` - Authorization dependencies (require_admin, require_role, etc.)
- `backend/app/core/exceptions.py` - PermissionDeniedException class
- `backend/app/services/authorization_service.py` - AuthorizationService with role hierarchy
- `backend/app/services/audit_service.py` - AuditService for security event logging
- `backend/app/middleware/tenant_context.py` - Tenant context injection middleware
- `backend/tests/unit/conftest.py` - Conftest overriding db fixture for unit tests
- `backend/tests/unit/test_authorization.py` - 38 authorization unit tests

**UPDATED Config:**
- `backend/pyproject.toml` - Added pytest pythonpath config for modern Python (no __init__.py needed)
