# Story 2.5: Implement User Management Endpoints for Admin/Supervisor

Status: Done

## Story

As an Admin or Supervisor,
I want to create, update, and manage user accounts for all roles,
So that I can onboard publishers, schools, teachers, and students to the platform (FR12-FR17, FR23-FR24).

## Acceptance Criteria

1. **Given** I am authenticated as Admin or Supervisor, **When** I send POST `/api/v1/users` with user data (email, password, role, tenant_id), **Then** a new user account is created with hashed password and assigned role

2. **Given** I am creating a user with tenant_id, **When** the tenant_id is provided, **Then** the tenant_id is validated to ensure it exists in the tenants table

3. **Given** user creation succeeds, **When** the response is returned, **Then** I receive 201 Created with user details (excluding password)

4. **Given** I am authenticated as Admin or Supervisor, **When** I send GET `/api/v1/users/{user_id}`, **Then** I receive user details including role, tenant_id, created_at

5. **Given** I am authenticated as Admin or Supervisor, **When** I send PATCH `/api/v1/users/{user_id}` to update role or deactivate account, **Then** the user record is updated and changes are logged in audit_logs

6. **Given** I am authenticated as Admin or Supervisor, **When** I send GET `/api/v1/users?role=publisher&page=1&page_size=50`, **Then** I receive a paginated list of users filtered by role (NFR-P1: <500ms)

7. **Given** I am authenticated as Admin or Supervisor, **When** I send GET `/api/v1/users?tenant_id={uuid}`, **Then** I receive users filtered by tenant

8. **Given** I am authenticated as Admin or Supervisor, **When** I send DELETE `/api/v1/users/{user_id}`, **Then** the user is deleted and the action is logged in audit_logs

9. **Given** a non-admin user, **When** attempting any admin user management endpoint, **Then** they receive 403 Forbidden with error_code "PERMISSION_DENIED"

10. **Given** Admin or Supervisor is managing users, **When** any create/update/delete operation succeeds, **Then** an audit log entry is created with action, user_id, target_user_id, and changes metadata

## Tasks / Subtasks

- [x] Task 1: Update User Creation with Tenant Validation (AC: #1, #2, #3)
  - [x] 1.1 UPDATE `backend/app/api/routes/users.py` create_user endpoint to validate tenant_id exists using `crud.get_tenant_by_id()`
  - [x] 1.2 ADD HTTPException 400 with error_code "TENANT_NOT_FOUND" if tenant_id doesn't exist
  - [x] 1.3 ALLOW Supervisor role (not just Admin) to create users via `require_supervisor_or_above` dependency
  - [x] 1.4 UPDATE response model to ensure password is never returned (verify UserPublic excludes hashed_password)
  - [x] 1.5 TEST tenant validation rejects invalid tenant_ids, accepts valid ones

- [x] Task 2: Implement Role and Tenant Filtering on List Users (AC: #6, #7)
  - [x] 2.1 UPDATE `backend/app/api/routes/users.py` read_users endpoint to accept `role` query parameter
  - [x] 2.2 ADD `tenant_id` query parameter for filtering users by tenant
  - [x] 2.3 IMPLEMENT filter logic in SQLModel query: `select(User).where(User.role == role).where(User.tenant_id == tenant_id)`
  - [x] 2.4 UPDATE dependencies to allow Supervisor role access via `require_supervisor_or_above`
  - [x] 2.5 TEST role filter returns only users with matching role
  - [x] 2.6 TEST tenant_id filter returns only users within that tenant
  - [x] 2.7 TEST combined filters (role + tenant_id) work correctly

- [x] Task 3: Enhance Get User by ID for Admin/Supervisor (AC: #4)
  - [x] 3.1 UPDATE `backend/app/api/routes/users.py` read_user_by_id endpoint to allow Supervisor access
  - [x] 3.2 ENSURE response includes role, tenant_id, created_at, updated_at fields (verify UserPublic schema)
  - [x] 3.3 ADD 404 Not Found with error_code "USER_NOT_FOUND" for non-existent user_id
  - [x] 3.4 TEST Admin can view any user details
  - [x] 3.5 TEST Supervisor can view any user details

- [x] Task 4: Implement Audit Logging for User Changes (AC: #5, #8, #10)
  - [x] 4.1 UPDATE `backend/app/api/routes/users.py` update_user to log changes via `crud.create_audit_log()`
  - [x] 4.2 ADD new AuditAction enum value "USER_UPDATE" in `backend/app/models.py`
  - [x] 4.3 ADD new AuditAction enum value "USER_CREATE" in `backend/app/models.py`
  - [x] 4.4 ADD new AuditAction enum value "USER_DELETE" in `backend/app/models.py`
  - [x] 4.5 UPDATE delete_user to log deletion via `crud.create_audit_log()`
  - [x] 4.6 UPDATE create_user to log creation via `crud.create_audit_log()`
  - [x] 4.7 INCLUDE metadata_json with changed fields (before/after values for updates)
  - [x] 4.8 TEST audit log created on user create with USER_CREATE action
  - [x] 4.9 TEST audit log created on user update with USER_UPDATE action and changed fields
  - [x] 4.10 TEST audit log created on user delete with USER_DELETE action

- [x] Task 5: Allow Supervisor Access to User Management (AC: #9)
  - [x] 5.1 UPDATE all admin-only dependencies to use `require_supervisor_or_above` instead of `require_admin`
  - [x] 5.2 VERIFY is_superuser flag still grants access (backward compatibility)
  - [x] 5.3 TEST Supervisor role can access all user management endpoints
  - [x] 5.4 TEST Publisher/Teacher/Student roles receive 403 Forbidden

- [x] Task 6: Implement User Deactivation (AC: #5)
  - [x] 6.1 VERIFY `is_active` field on User model works for deactivation
  - [x] 6.2 UPDATE update_user to accept is_active=false for deactivation
  - [x] 6.3 ADD logic to prevent login for deactivated users (verify in auth.py)
  - [x] 6.4 TEST setting is_active=false prevents user login
  - [x] 6.5 TEST reactivating user (is_active=true) allows login again

- [x] Task 7: Write Comprehensive Tests (AC: #1-#10)
  - [x] 7.1 CREATE `backend/tests/api/routes/test_users_admin.py` for admin user management tests
  - [x] 7.2 TEST POST /users creates user with valid tenant_id
  - [x] 7.3 TEST POST /users rejects invalid tenant_id with 400
  - [x] 7.4 TEST GET /users with role filter returns filtered results
  - [x] 7.5 TEST GET /users with tenant_id filter returns filtered results
  - [x] 7.6 TEST GET /users/{user_id} returns full user details
  - [x] 7.7 TEST PATCH /users/{user_id} updates role and creates audit log
  - [x] 7.8 TEST PATCH /users/{user_id} with is_active=false deactivates user
  - [x] 7.9 TEST DELETE /users/{user_id} removes user and creates audit log
  - [x] 7.10 TEST all endpoints return 403 for non-admin/supervisor users
  - [x] 7.11 TEST performance: list users with filters <500ms (NFR-P1)

## Dev Notes

### Architecture Compliance

**From Architecture Document (core-architectural-decisions.md):**

**Multi-Tenant Authorization Pattern:**
- Role Hierarchy: Admin/Supervisor have full access to all tenants (bypass RLS)
- User creation must validate tenant_id exists
- All CRUD operations must be logged in audit_logs for compliance

**Error Handling Standards:**
```json
{
  "error_code": "TENANT_NOT_FOUND",
  "message": "Tenant with ID {tenant_id} does not exist",
  "details": {"tenant_id": "uuid"},
  "request_id": "uuid-v4-request-id",
  "timestamp": "2025-12-15T10:30:00Z"
}
```

**Audit Logging:**
- Decision: Immutable append-only audit table in PostgreSQL
- Logged Events: All CRUD operations on users, permission changes, authentication events
- Schema: `audit_log(id, timestamp, user_id, action, resource_type, resource_id, metadata_json)`

### Existing Code Assets (REUSE from Stories 2.1-2.4)

**`backend/app/api/deps_auth.py`** - Authorization dependencies:
```python
require_admin(current_user: User) -> User
require_supervisor_or_above(current_user: User) -> User
require_role_or_above(minimum_role: UserRole) -> User
```

**`backend/app/crud.py`** - CRUD functions:
```python
create_user(session, user_create) -> User
update_user(session, db_user, user_in) -> User
get_user_by_email(session, email) -> User | None
get_tenant_by_id(session, tenant_id) -> Tenant | None
create_audit_log(session, audit_log_in) -> AuditLog
```

**`backend/app/models.py`** - Existing models:
```python
class UserRole(str, Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    PUBLISHER = "publisher"
    SCHOOL = "school"
    TEACHER = "teacher"
    STUDENT = "student"

class AuditAction(str, Enum):
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    RESTORE = "restore"
    UPDATE = "update"
    LOGIN = "login"
    LOGOUT = "logout"
    # ADD: USER_CREATE, USER_UPDATE, USER_DELETE
```

**`backend/app/api/routes/users.py`** - Current endpoints (10 total):
- GET `/users` - List users (Admin only)
- POST `/users` - Create user (Admin only)
- GET `/users/me` - Get current user
- PATCH `/users/me` - Update current user
- PATCH `/users/me/password` - Update password
- DELETE `/users/me` - Delete self
- POST `/users/signup` - Public registration
- GET `/users/{user_id}` - Get user by ID
- PATCH `/users/{user_id}` - Update user (Admin only)
- DELETE `/users/{user_id}` - Delete user (Admin only)

### Previous Story Intelligence (Story 2.4)

**Patterns Established:**
- Rate limiting applied to all user endpoints via `@limiter.limit(get_dynamic_rate_limit)`
- Request object required for rate limiter: `request: Request`
- Admin/Supervisor get unlimited API access (rate limit returns None)
- All routes use `CurrentUser` dependency for authentication

**Key Files from 2.1-2.4:**
- `backend/app/middleware/rate_limit.py` - Role-based rate limiting
- `backend/app/middleware/tenant_context.py` - JWT claims extraction
- `backend/app/api/deps.py` - CurrentUser dependency
- `backend/app/core/security.py` - JWT token handling

**Learnings from Previous Stories:**
- Use `require_supervisor_or_above` for endpoints accessible by both Admin and Supervisor
- Follow existing error response format with request_id
- Use structured JSON logging for audit/security events
- Rate limiting decorator must come AFTER route decorator

### Project Structure (UPDATE/CREATE)

**UPDATE Files:**
```
backend/app/api/routes/users.py        # ADD role/tenant filtering, tenant validation, audit logging
backend/app/models.py                  # ADD USER_CREATE, USER_UPDATE, USER_DELETE to AuditAction
```

**CREATE Files:**
```
backend/tests/api/routes/test_users_admin.py   # NEW: Admin user management tests
```

### Technical Implementation Details

**Tenant Validation on User Create:**
```python
# backend/app/api/routes/users.py

@router.post(
    "/",
    dependencies=[Depends(require_supervisor_or_above)],
    response_model=UserPublic,
    status_code=201,
)
@limiter.limit(get_dynamic_rate_limit)
def create_user(
    request: Request,
    *,
    session: SessionDep,
    user_in: UserCreate,
    current_user: CurrentUser,
) -> Any:
    """
    Create new user.

    Requires Admin or Supervisor role (Story 2.5).
    Rate limited - Admins/Supervisors have unlimited access.
    """
    # Validate tenant exists if provided
    if user_in.tenant_id:
        tenant = crud.get_tenant_by_id(session=session, tenant_id=user_in.tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "TENANT_NOT_FOUND",
                    "message": f"Tenant with ID {user_in.tenant_id} does not exist",
                    "details": {"tenant_id": str(user_in.tenant_id)},
                },
            )

    # Check email uniqueness
    existing_user = crud.get_user_by_email(session=session, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)

    # Create audit log for user creation
    crud.create_audit_log(
        session=session,
        audit_log_in=AuditLogCreate(
            action=AuditAction.USER_CREATE,
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            metadata_json={
                "target_user_id": str(user.id),
                "target_email": user.email,
                "target_role": user.role.value,
                "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            },
        ),
    )

    return user
```

**Role and Tenant Filtering:**
```python
# backend/app/api/routes/users.py

@router.get(
    "/",
    dependencies=[Depends(require_supervisor_or_above)],
    response_model=UsersPublic,
)
@limiter.limit(get_dynamic_rate_limit)
def read_users(
    request: Request,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    role: UserRole | None = None,
    tenant_id: uuid.UUID | None = None,
) -> Any:
    """
    Retrieve users with optional filtering.

    - **role**: Filter by user role (optional)
    - **tenant_id**: Filter by tenant (optional)

    Requires Admin or Supervisor role (Story 2.5).
    Rate limited - Admins/Supervisors have unlimited access.
    """
    # Build dynamic query with filters
    statement = select(User)

    if role:
        statement = statement.where(User.role == role)

    if tenant_id:
        statement = statement.where(User.tenant_id == tenant_id)

    # Get count for pagination
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)
```

**Audit Logging for User Updates:**
```python
# backend/app/api/routes/users.py

@router.patch(
    "/{user_id}",
    dependencies=[Depends(require_supervisor_or_above)],
    response_model=UserPublic,
)
@limiter.limit(get_dynamic_rate_limit)
def update_user(
    request: Request,
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update a user.

    Requires Admin or Supervisor role (Story 2.5).
    Changes are logged in audit_logs.
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} does not exist",
                "details": {"user_id": str(user_id)},
            },
        )

    # Capture changes for audit log
    changes = {}
    update_data = user_in.model_dump(exclude_unset=True)
    for field, new_value in update_data.items():
        old_value = getattr(db_user, field, None)
        if old_value != new_value:
            changes[field] = {"old": str(old_value), "new": str(new_value)}

    # Validate email uniqueness if changing
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409,
                detail="User with this email already exists",
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)

    # Create audit log for user update
    crud.create_audit_log(
        session=session,
        audit_log_in=AuditLogCreate(
            action=AuditAction.USER_UPDATE,
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            metadata_json={
                "target_user_id": str(user_id),
                "changes": changes,
            },
        ),
    )

    return db_user
```

**New AuditAction Enum Values:**
```python
# backend/app/models.py

class AuditAction(str, Enum):
    """Actions tracked in audit logs."""

    # Asset actions
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    RESTORE = "restore"
    UPDATE = "update"

    # Auth actions
    LOGIN = "login"
    LOGOUT = "logout"

    # User management actions (Story 2.5)
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
```

### Dependencies

**Already Available (from pyproject.toml):**
```
fastapi
sqlmodel
pydantic
slowapi (for rate limiting)
```

**No New Dependencies Required**

### Git Workflow

**Branch:** `story/2-5-user-management-admin`

**Commit Pattern (following previous stories):**
```
feat(story-2.5): Implement user management endpoints for Admin/Supervisor
```

### Testing Standards

**Test Commands:**
```bash
# Run admin user management tests
uv run pytest backend/tests/api/routes/test_users_admin.py -v

# Run with coverage
uv run pytest backend/tests/api/routes/test_users_admin.py -v --cov=backend/app/api/routes/users

# Test all user-related tests
uv run pytest backend/tests/ -v -k "user"
```

**Key Test Cases:**
```python
# backend/tests/api/routes/test_users_admin.py

class TestUserCreationWithTenant:
    def test_create_user_with_valid_tenant_id(self, admin_client, valid_tenant):
        """POST /users with valid tenant_id creates user."""
        response = admin_client.post("/api/v1/users", json={
            "email": "newuser@example.com",
            "password": "ValidPass123!",
            "role": "teacher",
            "tenant_id": str(valid_tenant.id),
        })
        assert response.status_code == 201
        assert response.json()["tenant_id"] == str(valid_tenant.id)

    def test_create_user_with_invalid_tenant_id_returns_400(self, admin_client):
        """POST /users with non-existent tenant_id returns 400."""
        fake_tenant_id = str(uuid.uuid4())
        response = admin_client.post("/api/v1/users", json={
            "email": "newuser@example.com",
            "password": "ValidPass123!",
            "role": "teacher",
            "tenant_id": fake_tenant_id,
        })
        assert response.status_code == 400
        assert response.json()["detail"]["error_code"] == "TENANT_NOT_FOUND"


class TestUserFiltering:
    def test_filter_users_by_role(self, admin_client, users_with_roles):
        """GET /users?role=teacher returns only teachers."""
        response = admin_client.get("/api/v1/users", params={"role": "teacher"})
        assert response.status_code == 200
        for user in response.json()["data"]:
            assert user["role"] == "teacher"

    def test_filter_users_by_tenant(self, admin_client, users_with_tenants):
        """GET /users?tenant_id={id} returns only users in that tenant."""
        tenant_id = users_with_tenants[0].tenant_id
        response = admin_client.get("/api/v1/users", params={"tenant_id": str(tenant_id)})
        assert response.status_code == 200
        for user in response.json()["data"]:
            assert user["tenant_id"] == str(tenant_id)


class TestAuditLogging:
    def test_user_create_creates_audit_log(self, admin_client, session, valid_tenant):
        """POST /users creates audit log with USER_CREATE action."""
        response = admin_client.post("/api/v1/users", json={...})
        assert response.status_code == 201

        # Verify audit log
        audit_logs = crud.get_audit_logs_by_user(session, admin_user_id)
        assert any(log.action == AuditAction.USER_CREATE for log in audit_logs)

    def test_user_update_logs_changes(self, admin_client, session, test_user):
        """PATCH /users/{id} logs changed fields in audit log."""
        response = admin_client.patch(
            f"/api/v1/users/{test_user.id}",
            json={"role": "publisher"}
        )
        assert response.status_code == 200

        # Verify audit log contains changes
        audit_logs = crud.get_audit_logs_by_user(session, admin_user_id)
        update_log = next(l for l in audit_logs if l.action == AuditAction.USER_UPDATE)
        assert "role" in update_log.metadata_json["changes"]


class TestSupervisorAccess:
    def test_supervisor_can_create_users(self, supervisor_client, valid_tenant):
        """Supervisor role can create users."""
        response = supervisor_client.post("/api/v1/users", json={...})
        assert response.status_code == 201

    def test_supervisor_can_list_users(self, supervisor_client):
        """Supervisor role can list users."""
        response = supervisor_client.get("/api/v1/users")
        assert response.status_code == 200

    def test_publisher_cannot_create_users(self, publisher_client, valid_tenant):
        """Publisher role receives 403 on user creation."""
        response = publisher_client.post("/api/v1/users", json={...})
        assert response.status_code == 403
```

### Security Considerations

**Critical Security Requirements:**
- Never return hashed_password in API responses (verify UserPublic schema)
- Validate tenant_id exists before creating user
- Only Admin/Supervisor can manage users
- All user management operations must be audit logged

**OWASP Compliance:**
- A1:2021 - Broken Access Control: Role-based access enforced
- A7:2021 - Identification and Authentication Failures: Strong password requirements maintained
- A9:2021 - Security Logging and Monitoring: Audit logs for all user management

### Integration Notes

**This story prepares foundation for:**
- Story 2.6: Supervisor Tenant-Scoped Access (if applicable)
- Epic 3: Asset Upload/Download (users can be assigned to tenants)
- Epic 6: LMS Integration (user management via API)

**Backward Compatibility:**
- Existing admin endpoints keep working (is_superuser flag)
- Existing login/auth flows unchanged
- Public signup endpoint unaffected

## References

- [Source: docs/epics.md#Story-2.5] - Original story requirements
- [Source: docs/architecture/core-architectural-decisions.md#Multi-Tenant-Authorization-Pattern] - Authorization specifications
- [Source: docs/architecture/core-architectural-decisions.md#Audit-Logging] - Audit logging requirements
- [Source: docs/sprint-artifacts/2-4-implement-rate-limiting-per-user-role.md] - Previous story patterns

## Dev Agent Record

### Context Reference

Story 2.5 implementation - fifth story in Epic 2 (User Authentication & Authorization).
Extends user management endpoints with tenant validation, role filtering, and audit logging.
Builds on authorization dependencies from Story 2.2 and rate limiting from Story 2.4.

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

**Task 1-3 (Previously Completed):**
- User creation with tenant validation implemented and tested
- Role and tenant filtering on list users implemented and tested
- Get user by ID enhanced with proper 404 handling

**Task 4 (Audit Logging):**
- All user management operations (create, update, delete) now log to audit_log table
- AuditAction enum extended with USER_CREATE, USER_UPDATE, USER_DELETE values
- Update operations include before/after values in metadata_json
- Audit log only created when actual changes occur (no-op updates skip logging)
- 5 audit logging tests added and passing

**Task 5 (Supervisor Access):**
- All admin endpoints use `require_supervisor_or_above` dependency
- Backward compatibility maintained via is_superuser flag
- Publisher/Teacher/Student roles correctly receive 403 Forbidden
- 6 supervisor access tests passing

**Task 6 (User Deactivation):**
- is_active field works for deactivation via PATCH endpoint
- Login correctly blocked for deactivated users
- Reactivation restores login capability
- 3 deactivation tests passing

**Task 7 (Comprehensive Tests):**
- Created test_users_admin.py with 31 tests total
- All acceptance criteria covered with tests
- Performance test confirms <500ms response time (NFR-P1)
- All 56 user-related tests pass (31 admin + 25 existing)

### File List

**Modified:**
- `backend/app/api/routes/users.py` - Tenant validation, role/tenant filtering, audit logging for all CRUD operations
- `backend/app/models.py` - Added user_create, user_update, user_delete to AuditAction enum
- `backend/app/main.py` - Enhanced HTTP exception handler for structured error responses (TENANT_NOT_FOUND, USER_NOT_FOUND)
- `backend/tests/api/routes/test_users.py` - Updated 2 existing tests for Story 2.5 behavior changes

**Created:**
- `backend/tests/api/routes/test_users_admin.py` - Comprehensive admin user management tests (31 tests)
- `backend/app/alembic/versions/add_user_audit_actions.py` - Migration to add user management audit actions to PostgreSQL enum

### Change Log

- 2025-12-17: Code review fixes - H1 (import location), H2 (enum casing), M1-M3 (file list updated)
- 2025-12-17: Story completed - All 7 tasks implemented and tested, 31 new tests pass
- 2025-12-17: Added audit logging tests (Task 4.8, 4.9, 4.10) and comprehensive tests (Task 7)
- 2025-12-16: Validation fix - Removed Task 7 (Tenant CRUD) as scope creep; renumbered Task 8 to Task 7
- 2025-12-16: Draft story created by Scrum Master (Bob)
