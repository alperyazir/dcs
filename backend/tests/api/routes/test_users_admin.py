"""
Admin User Management Tests (Story 2.5)

Tests for admin/supervisor user management endpoints including:
- Tenant validation on user creation (Task 1)
- Role and tenant filtering (Task 2)
- Audit logging for user changes (Task 4)
- Supervisor access to user management (Task 5)
- User deactivation (Task 6)
"""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    AuditLog,
    Tenant,
    TenantCreate,
    TenantType,
    User,
    UserCreate,
    UserRole,
)
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def test_tenant(db: Session) -> Tenant:
    """Create a test tenant for user creation tests."""
    tenant_in = TenantCreate(
        name=f"test-tenant-{random_lower_string()[:8]}",
        tenant_type=TenantType.SCHOOL,
    )
    tenant = crud.create_tenant(session=db, tenant_in=tenant_in)
    return tenant


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for testing."""
    email = f"admin-{random_lower_string()[:8]}@test.com"
    user_in = UserCreate(
        email=email,
        password="AdminPass123!",
        role=UserRole.ADMIN,
    )
    user = crud.create_user(session=db, user_create=user_in)
    return user


@pytest.fixture
def admin_token_headers(client: TestClient, admin_user: User) -> dict[str, str]:
    """Get authentication headers for admin user."""
    return user_authentication_headers(
        client=client,
        email=admin_user.email,
        password="AdminPass123!",
    )


@pytest.fixture
def supervisor_user(db: Session) -> User:
    """Create a supervisor user for testing."""
    email = f"supervisor-{random_lower_string()[:8]}@test.com"
    user_in = UserCreate(
        email=email,
        password="SupervisorPass123!",
        role=UserRole.SUPERVISOR,
    )
    user = crud.create_user(session=db, user_create=user_in)
    return user


@pytest.fixture
def supervisor_token_headers(
    client: TestClient, supervisor_user: User
) -> dict[str, str]:
    """Get authentication headers for supervisor user."""
    return user_authentication_headers(
        client=client,
        email=supervisor_user.email,
        password="SupervisorPass123!",
    )


@pytest.fixture
def publisher_user(db: Session) -> User:
    """Create a publisher user for testing."""
    email = f"publisher-{random_lower_string()[:8]}@test.com"
    user_in = UserCreate(
        email=email,
        password="PublisherPass123!",
        role=UserRole.PUBLISHER,
    )
    user = crud.create_user(session=db, user_create=user_in)
    return user


@pytest.fixture
def publisher_token_headers(client: TestClient, publisher_user: User) -> dict[str, str]:
    """Get authentication headers for publisher user."""
    return user_authentication_headers(
        client=client,
        email=publisher_user.email,
        password="PublisherPass123!",
    )


@pytest.fixture
def teacher_user(db: Session, test_tenant: Tenant) -> User:
    """Create a teacher user for testing."""
    email = f"teacher-{random_lower_string()[:8]}@test.com"
    user_in = UserCreate(
        email=email,
        password="TeacherPass123!",
        role=UserRole.TEACHER,
        tenant_id=test_tenant.id,
    )
    user = crud.create_user(session=db, user_create=user_in)
    return user


# =============================================================================
# TASK 1: USER CREATION WITH TENANT VALIDATION (AC: #1, #2, #3)
# =============================================================================


class TestUserCreationWithTenant:
    """Tests for user creation with tenant validation (Task 1)."""

    def test_create_user_with_valid_tenant_id(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_tenant: Tenant,
        db: Session,
    ) -> None:
        """POST /users with valid tenant_id creates user (AC: #1, #2)."""
        email = random_email()
        with patch("app.utils.send_email", return_value=None):
            response = client.post(
                f"{settings.API_V1_STR}/users/",
                headers=superuser_token_headers,
                json={
                    "email": email,
                    "password": "ValidPass123!",
                    "role": "teacher",
                    "tenant_id": str(test_tenant.id),
                },
            )
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.json()}"
        data = response.json()
        assert data["email"] == email
        assert data["tenant_id"] == str(test_tenant.id)
        assert data["role"] == "teacher"
        # Verify password is not returned (AC: #3)
        assert "password" not in data
        assert "hashed_password" not in data

    def test_create_user_with_invalid_tenant_id_returns_400(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """POST /users with non-existent tenant_id returns 400 (AC: #2)."""
        fake_tenant_id = str(uuid.uuid4())
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            json={
                "email": random_email(),
                "password": "ValidPass123!",
                "role": "teacher",
                "tenant_id": fake_tenant_id,
            },
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "TENANT_NOT_FOUND"
        assert fake_tenant_id in detail["message"]

    def test_create_user_without_tenant_id_succeeds(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """POST /users without tenant_id creates user (tenant is optional)."""
        email = random_email()
        with patch("app.utils.send_email", return_value=None):
            response = client.post(
                f"{settings.API_V1_STR}/users/",
                headers=superuser_token_headers,
                json={
                    "email": email,
                    "password": "ValidPass123!",
                    "role": "publisher",
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert data["tenant_id"] is None

    def test_create_user_returns_201_status_code(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """POST /users returns 201 Created (AC: #3)."""
        with patch("app.utils.send_email", return_value=None):
            response = client.post(
                f"{settings.API_V1_STR}/users/",
                headers=superuser_token_headers,
                json={
                    "email": random_email(),
                    "password": "ValidPass123!",
                },
            )
        assert response.status_code == 201

    def test_supervisor_can_create_users(
        self,
        client: TestClient,
        supervisor_token_headers: dict[str, str],
        test_tenant: Tenant,
    ) -> None:
        """Supervisor role can create users (Task 1.3)."""
        email = random_email()
        with patch("app.utils.send_email", return_value=None):
            response = client.post(
                f"{settings.API_V1_STR}/users/",
                headers=supervisor_token_headers,
                json={
                    "email": email,
                    "password": "ValidPass123!",
                    "role": "teacher",
                    "tenant_id": str(test_tenant.id),
                },
            )
        assert response.status_code == 201
        assert response.json()["email"] == email


# =============================================================================
# TASK 2: ROLE AND TENANT FILTERING (AC: #6, #7)
# =============================================================================


class TestUserFiltering:
    """Tests for user filtering by role and tenant (Task 2)."""

    def test_filter_users_by_role(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        teacher_user: User,
        db: Session,
    ) -> None:
        """GET /users?role=teacher returns only teachers (AC: #6)."""
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            params={"role": "teacher"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        for user in data["data"]:
            assert user["role"] == "teacher"

    def test_filter_users_by_tenant_id(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        teacher_user: User,
        test_tenant: Tenant,
    ) -> None:
        """GET /users?tenant_id={id} returns only users in that tenant (AC: #7)."""
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            params={"tenant_id": str(test_tenant.id)},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        for user in data["data"]:
            assert user["tenant_id"] == str(test_tenant.id)

    def test_filter_users_by_role_and_tenant_combined(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        teacher_user: User,
        test_tenant: Tenant,
    ) -> None:
        """GET /users?role=teacher&tenant_id={id} returns filtered results."""
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            params={"role": "teacher", "tenant_id": str(test_tenant.id)},
        )
        assert response.status_code == 200
        data = response.json()
        for user in data["data"]:
            assert user["role"] == "teacher"
            assert user["tenant_id"] == str(test_tenant.id)

    def test_supervisor_can_list_users(
        self,
        client: TestClient,
        supervisor_token_headers: dict[str, str],
    ) -> None:
        """Supervisor role can list users (Task 2.4)."""
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=supervisor_token_headers,
        )
        assert response.status_code == 200


# =============================================================================
# TASK 3: GET USER BY ID (AC: #4)
# =============================================================================


class TestGetUserById:
    """Tests for getting user by ID (Task 3)."""

    def test_get_user_by_id_returns_full_details(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        teacher_user: User,
    ) -> None:
        """GET /users/{user_id} returns role, tenant_id, created_at (AC: #4)."""
        response = client.get(
            f"{settings.API_V1_STR}/users/{teacher_user.id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "teacher"
        assert "tenant_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_nonexistent_user_returns_404(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """GET /users/{nonexistent_id} returns 404 (Task 3.3)."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"{settings.API_V1_STR}/users/{fake_id}",
            headers=superuser_token_headers,
        )
        # Current implementation returns 200 with None or similar
        # After fix, should return 404
        assert response.status_code == 404

    def test_supervisor_can_view_any_user(
        self,
        client: TestClient,
        supervisor_token_headers: dict[str, str],
        teacher_user: User,
    ) -> None:
        """Supervisor can view any user details (Task 3.5)."""
        response = client.get(
            f"{settings.API_V1_STR}/users/{teacher_user.id}",
            headers=supervisor_token_headers,
        )
        assert response.status_code == 200


# =============================================================================
# TASK 5: SUPERVISOR ACCESS (AC: #9)
# =============================================================================


class TestSupervisorAccess:
    """Tests for supervisor access to user management (Task 5)."""

    def test_publisher_cannot_create_users(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
    ) -> None:
        """Publisher role receives 403 on user creation (AC: #9)."""
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=publisher_token_headers,
            json={
                "email": random_email(),
                "password": "ValidPass123!",
            },
        )
        assert response.status_code == 403

    def test_publisher_cannot_list_users(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
    ) -> None:
        """Publisher role receives 403 on listing users (AC: #9)."""
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=publisher_token_headers,
        )
        assert response.status_code == 403

    def test_publisher_cannot_update_other_users(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        teacher_user: User,
    ) -> None:
        """Publisher role receives 403 on updating other users (AC: #9)."""
        response = client.patch(
            f"{settings.API_V1_STR}/users/{teacher_user.id}",
            headers=publisher_token_headers,
            json={"full_name": "Hacked Name"},
        )
        assert response.status_code == 403

    def test_publisher_cannot_delete_users(
        self,
        client: TestClient,
        publisher_token_headers: dict[str, str],
        teacher_user: User,
    ) -> None:
        """Publisher role receives 403 on deleting users (AC: #9)."""
        response = client.delete(
            f"{settings.API_V1_STR}/users/{teacher_user.id}",
            headers=publisher_token_headers,
        )
        assert response.status_code == 403

    def test_supervisor_can_update_users(
        self,
        client: TestClient,
        supervisor_token_headers: dict[str, str],
        teacher_user: User,
    ) -> None:
        """Supervisor can update users (Task 5.3)."""
        response = client.patch(
            f"{settings.API_V1_STR}/users/{teacher_user.id}",
            headers=supervisor_token_headers,
            json={"full_name": "Updated by Supervisor"},
        )
        assert response.status_code == 200

    def test_supervisor_can_delete_users(
        self,
        client: TestClient,
        supervisor_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Supervisor can delete users (Task 5.3)."""
        # Create a user to delete
        email = random_email()
        user_in = UserCreate(email=email, password="ToDelete123!")
        user = crud.create_user(session=db, user_create=user_in)

        response = client.delete(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=supervisor_token_headers,
        )
        assert response.status_code == 200


# =============================================================================
# TASK 6: USER DEACTIVATION (AC: #5)
# =============================================================================


class TestUserDeactivation:
    """Tests for user deactivation (Task 6)."""

    def test_deactivate_user_via_update(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """PATCH /users/{id} with is_active=false deactivates user (AC: #5)."""
        # Create a user to deactivate
        email = random_email()
        user_in = UserCreate(email=email, password="ToDeactivate123!")
        user = crud.create_user(session=db, user_create=user_in)

        response = client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
            json={"is_active": False},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_deactivated_user_cannot_login(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Deactivated user cannot login (Task 6.4)."""
        # Create and deactivate user
        email = random_email()
        password = "ToDeactivate123!"
        user_in = UserCreate(email=email, password=password)
        user = crud.create_user(session=db, user_create=user_in)

        # Deactivate
        client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
            json={"is_active": False},
        )

        # Try to login
        login_response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            data={"username": email, "password": password},
        )
        assert login_response.status_code == 400

    def test_reactivated_user_can_login(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Reactivated user can login again (Task 6.5)."""
        # Create, deactivate, then reactivate user
        email = random_email()
        password = "ToReactivate123!"
        user_in = UserCreate(email=email, password=password)
        user = crud.create_user(session=db, user_create=user_in)

        # Deactivate
        client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
            json={"is_active": False},
        )

        # Reactivate
        client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
            json={"is_active": True},
        )

        # Try to login
        login_response = client.post(
            f"{settings.API_V1_STR}/login/access-token",
            data={"username": email, "password": password},
        )
        assert login_response.status_code == 200


# =============================================================================
# TASK 4: AUDIT LOGGING (AC: #5, #8, #10)
# =============================================================================


class TestAuditLogging:
    """Tests for audit logging on user management operations (Task 4)."""

    def test_user_create_creates_audit_log(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_tenant: Tenant,
        db: Session,
    ) -> None:
        """POST /users creates audit log with USER_CREATE action (Task 4.8)."""
        email = random_email()
        with patch("app.utils.send_email", return_value=None):
            response = client.post(
                f"{settings.API_V1_STR}/users/",
                headers=superuser_token_headers,
                json={
                    "email": email,
                    "password": "AuditTest123!",
                    "role": "teacher",
                    "tenant_id": str(test_tenant.id),
                },
            )
        assert response.status_code == 201
        created_user_id = response.json()["id"]

        # Verify audit log was created
        audit_logs = db.exec(
            select(AuditLog).where(AuditLog.action == "user_create")
        ).all()
        matching_log = next(
            (
                log
                for log in audit_logs
                if log.metadata_json
                and log.metadata_json.get("target_user_id") == created_user_id
            ),
            None,
        )
        assert matching_log is not None, "Audit log for USER_CREATE not found"
        assert matching_log.metadata_json["target_email"] == email
        assert matching_log.metadata_json["target_role"] == "teacher"
        assert matching_log.metadata_json["tenant_id"] == str(test_tenant.id)

    def test_user_update_creates_audit_log_with_changes(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """PATCH /users/{id} logs changed fields in audit log (Task 4.9)."""
        # Create a user to update
        email = random_email()
        user_in = UserCreate(email=email, password="ToUpdate123!")
        user = crud.create_user(session=db, user_create=user_in)

        # Update the user's full_name
        response = client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
            json={"full_name": "Updated Name For Audit"},
        )
        assert response.status_code == 200

        # Verify audit log was created with changes
        audit_logs = db.exec(
            select(AuditLog).where(AuditLog.action == "user_update")
        ).all()
        matching_log = next(
            (
                log
                for log in audit_logs
                if log.metadata_json
                and log.metadata_json.get("target_user_id") == str(user.id)
            ),
            None,
        )
        assert matching_log is not None, "Audit log for user_update not found"
        assert "changes" in matching_log.metadata_json
        assert "full_name" in matching_log.metadata_json["changes"]
        assert (
            matching_log.metadata_json["changes"]["full_name"]["new"]
            == "Updated Name For Audit"
        )

    def test_user_update_role_logs_changes(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """PATCH /users/{id} updates role and creates audit log (AC: #5, Task 7.7)."""
        # Create a user with student role
        email = random_email()
        user_in = UserCreate(
            email=email, password="RoleChange123!", role=UserRole.STUDENT
        )
        user = crud.create_user(session=db, user_create=user_in)

        # Update to publisher role
        response = client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
            json={"role": "publisher"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "publisher"

        # Verify audit log was created with role change
        audit_logs = db.exec(
            select(AuditLog).where(AuditLog.action == "user_update")
        ).all()
        matching_log = next(
            (
                log
                for log in audit_logs
                if log.metadata_json
                and log.metadata_json.get("target_user_id") == str(user.id)
                and "role" in log.metadata_json.get("changes", {})
            ),
            None,
        )
        assert matching_log is not None, "Audit log for role change not found"
        assert matching_log.metadata_json["changes"]["role"]["old"] == "student"
        assert matching_log.metadata_json["changes"]["role"]["new"] == "publisher"

    def test_user_delete_creates_audit_log(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """DELETE /users/{id} creates audit log with USER_DELETE action (Task 4.10, Task 7.9)."""
        # Create a user to delete
        email = random_email()
        user_in = UserCreate(
            email=email, password="ToDelete123!", role=UserRole.TEACHER
        )
        user = crud.create_user(session=db, user_create=user_in)
        user_id = str(user.id)

        response = client.delete(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200

        # Verify audit log was created
        audit_logs = db.exec(
            select(AuditLog).where(AuditLog.action == "user_delete")
        ).all()
        matching_log = next(
            (
                log
                for log in audit_logs
                if log.metadata_json
                and log.metadata_json.get("target_user_id") == user_id
            ),
            None,
        )
        assert matching_log is not None, "Audit log for user_delete not found"
        assert matching_log.metadata_json["target_email"] == email
        assert matching_log.metadata_json["target_role"] == "teacher"

    def test_user_update_no_changes_no_audit_log(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """PATCH /users/{id} with no actual changes does not create audit log."""
        # Create a user
        email = random_email()
        user_in = UserCreate(
            email=email, password="NoChange123!", full_name="Same Name"
        )
        user = crud.create_user(session=db, user_create=user_in)

        # Count existing audit logs for this user
        existing_logs = db.exec(
            select(AuditLog).where(AuditLog.action == "user_update")
        ).all()
        existing_count = len(
            [
                log
                for log in existing_logs
                if log.metadata_json
                and log.metadata_json.get("target_user_id") == str(user.id)
            ]
        )

        # Update with same value (no actual change)
        response = client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=superuser_token_headers,
            json={"full_name": "Same Name"},
        )
        assert response.status_code == 200

        # Verify no new audit log was created
        new_logs = db.exec(
            select(AuditLog).where(AuditLog.action == "user_update")
        ).all()
        new_count = len(
            [
                log
                for log in new_logs
                if log.metadata_json
                and log.metadata_json.get("target_user_id") == str(user.id)
            ]
        )
        assert (
            new_count == existing_count
        ), "Audit log should not be created for no-op update"


# =============================================================================
# TASK 7: ADDITIONAL COMPREHENSIVE TESTS (AC: #1-#10)
# =============================================================================


class TestComprehensiveUserManagement:
    """Additional comprehensive tests for user management (Task 7)."""

    def test_list_users_pagination(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """GET /users supports pagination with skip and limit."""
        # Create multiple users
        for i in range(5):
            user_in = UserCreate(
                email=f"pagination-{i}-{random_lower_string()[:4]}@test.com",
                password="Pagination123!",
            )
            crud.create_user(session=db, user_create=user_in)

        # Test pagination
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            params={"skip": 0, "limit": 2},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 2
        assert data["count"] >= 5  # At least the 5 we created

    def test_list_users_performance(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
    ) -> None:
        """GET /users with filters responds in <500ms (NFR-P1, Task 7.11)."""
        import time

        start = time.time()
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers=superuser_token_headers,
            params={"role": "teacher", "limit": 50},
        )
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 500, f"Response took {elapsed_ms:.0f}ms, expected <500ms"

    def test_admin_can_access_all_user_endpoints(
        self,
        client: TestClient,
        admin_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Admin role can access all user management endpoints (Task 5.2)."""
        # Create a test user
        email = random_email()
        user_in = UserCreate(email=email, password="AdminAccess123!")
        user = crud.create_user(session=db, user_create=user_in)

        # Test all admin endpoints
        # List users
        r = client.get(f"{settings.API_V1_STR}/users/", headers=admin_token_headers)
        assert r.status_code == 200

        # Get user by ID
        r = client.get(
            f"{settings.API_V1_STR}/users/{user.id}", headers=admin_token_headers
        )
        assert r.status_code == 200

        # Update user
        r = client.patch(
            f"{settings.API_V1_STR}/users/{user.id}",
            headers=admin_token_headers,
            json={"full_name": "Admin Updated"},
        )
        assert r.status_code == 200

        # Delete user
        r = client.delete(
            f"{settings.API_V1_STR}/users/{user.id}", headers=admin_token_headers
        )
        assert r.status_code == 200

    def test_teacher_cannot_access_admin_endpoints(
        self,
        client: TestClient,
        db: Session,
        test_tenant: Tenant,
    ) -> None:
        """Teacher role receives 403 on all admin endpoints (AC: #9, Task 5.4)."""
        # Create a teacher user and get auth headers
        email = f"teacher-perm-{random_lower_string()[:8]}@test.com"
        user_in = UserCreate(
            email=email,
            password="TeacherPerm123!",
            role=UserRole.TEACHER,
            tenant_id=test_tenant.id,
        )
        crud.create_user(session=db, user_create=user_in)

        teacher_headers = user_authentication_headers(
            client=client, email=email, password="TeacherPerm123!"
        )

        # Create another user to test against
        other_user_in = UserCreate(email=random_email(), password="Other123!")
        other_user = crud.create_user(session=db, user_create=other_user_in)

        # Test all admin endpoints return 403
        r = client.get(f"{settings.API_V1_STR}/users/", headers=teacher_headers)
        assert r.status_code == 403

        r = client.post(
            f"{settings.API_V1_STR}/users/",
            headers=teacher_headers,
            json={"email": random_email(), "password": "Test123!"},
        )
        assert r.status_code == 403

        r = client.patch(
            f"{settings.API_V1_STR}/users/{other_user.id}",
            headers=teacher_headers,
            json={"full_name": "Hacked"},
        )
        assert r.status_code == 403

        r = client.delete(
            f"{settings.API_V1_STR}/users/{other_user.id}",
            headers=teacher_headers,
        )
        assert r.status_code == 403

    def test_student_cannot_access_admin_endpoints(
        self,
        client: TestClient,
        db: Session,
        test_tenant: Tenant,
    ) -> None:
        """Student role receives 403 on all admin endpoints (AC: #9, Task 5.4)."""
        # Create a student user and get auth headers
        email = f"student-perm-{random_lower_string()[:8]}@test.com"
        user_in = UserCreate(
            email=email,
            password="StudentPerm123!",
            role=UserRole.STUDENT,
            tenant_id=test_tenant.id,
        )
        crud.create_user(session=db, user_create=user_in)

        student_headers = user_authentication_headers(
            client=client, email=email, password="StudentPerm123!"
        )

        # Test admin endpoint returns 403
        r = client.get(f"{settings.API_V1_STR}/users/", headers=student_headers)
        assert r.status_code == 403
