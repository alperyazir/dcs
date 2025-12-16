"""
Authorization service for role-based access control (Story 2.2).

Provides:
- Role hierarchy constants and helpers (Task 1.3, 1.4)
- Resource ownership validation (Task 3)
- Storage path access control (Task 8)

References:
- AC: #1-#6 (role-based resource access)
- AC: #10 (reusable authorization functions)
"""

from uuid import UUID

from app.core.exceptions import PermissionDeniedException
from app.models import User, UserRole

# =============================================================================
# ROLE HIERARCHY (Task 1.3)
# =============================================================================

ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.ADMIN: 6,
    UserRole.SUPERVISOR: 5,
    UserRole.PUBLISHER: 4,
    UserRole.SCHOOL: 3,
    UserRole.TEACHER: 2,
    UserRole.STUDENT: 1,
}

# Mapping of storage path prefixes to required roles (Task 3.3)
OWNER_TYPE_TO_ROLE: dict[str, UserRole] = {
    "publishers": UserRole.PUBLISHER,
    "schools": UserRole.SCHOOL,
    "teachers": UserRole.TEACHER,
    "students": UserRole.STUDENT,
}


# =============================================================================
# ROLE HIERARCHY HELPER (Task 1.4)
# =============================================================================


def has_role_or_higher(user_role: UserRole, required_role: UserRole) -> bool:
    """
    Check if user_role is equal to or higher than required_role in hierarchy.

    Args:
        user_role: The user's current role
        required_role: The minimum required role

    Returns:
        True if user_role >= required_role in the hierarchy

    Example:
        has_role_or_higher(UserRole.ADMIN, UserRole.TEACHER) -> True
        has_role_or_higher(UserRole.STUDENT, UserRole.TEACHER) -> False
    """
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


# =============================================================================
# AUTHORIZATION SERVICE (Task 3)
# =============================================================================


class AuthorizationService:
    """
    Service for validating resource ownership and access permissions.

    Implements:
    - Resource ownership validation (AC: #3, #4, #5, #6)
    - Admin/Supervisor bypass (AC: #2)
    - Storage path access control (AC: #3-#6)
    """

    @staticmethod
    def validate_resource_ownership(
        user: User,
        resource_owner_id: UUID,
        resource_owner_type: str,
    ) -> bool:
        """
        Check if user can access/modify resource based on ownership.

        Args:
            user: The authenticated user
            resource_owner_id: UUID of the resource owner
            resource_owner_type: Type of owner (publishers, schools, teachers, students)

        Returns:
            True if user has access, False otherwise

        Rules:
            - Admin/Supervisor: Always True (bypass all checks)
            - Others: Must have matching role AND matching ID
        """
        # Admin/Supervisor bypass all ownership checks (AC: #2)
        if user.role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
            return True

        # Map owner type to expected role
        expected_role = OWNER_TYPE_TO_ROLE.get(resource_owner_type)
        if not expected_role:
            return False

        # User must have matching role AND matching ID (AC: #3-#6)
        return user.role == expected_role and user.id == resource_owner_id

    @staticmethod
    def get_allowed_storage_prefix(user: User) -> str:
        """
        Get the storage path prefix user can write to.

        Args:
            user: The authenticated user

        Returns:
            Path prefix string (e.g., "/publishers/{uuid}/")

        Rules:
            - Admin/Supervisor: "/" (full access)
            - Others: "/{role_plural}/{user_id}/"
        """
        role_to_prefix: dict[UserRole, str] = {
            UserRole.ADMIN: "/",
            UserRole.SUPERVISOR: "/",
            UserRole.PUBLISHER: f"/publishers/{user.id}/",
            UserRole.SCHOOL: f"/schools/{user.id}/",
            UserRole.TEACHER: f"/teachers/{user.id}/",
            UserRole.STUDENT: f"/students/{user.id}/",
        }
        return role_to_prefix.get(user.role, "")

    @staticmethod
    def can_write_to_path(user: User, object_path: str) -> bool:
        """
        Check if user can write to given object path.

        Args:
            user: The authenticated user
            object_path: Full path to the object (e.g., "/publishers/123/file.pdf")

        Returns:
            True if user can write to the path

        Rules:
            - Admin/Supervisor: Can write anywhere
            - Others: Path must start with their allowed prefix
        """
        # Admin/Supervisor bypass (AC: #2)
        if user.role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
            return True

        allowed_prefix = AuthorizationService.get_allowed_storage_prefix(user)
        return object_path.startswith(allowed_prefix)

    @staticmethod
    def parse_path_ownership(object_path: str) -> tuple[str | None, UUID | None]:
        """
        Parse object path to extract owner_type and owner_id.

        Args:
            object_path: Path like "/publishers/123-456/file.pdf"

        Returns:
            Tuple of (owner_type, owner_id) or (None, None) if invalid
        """
        # Remove leading slash and split
        parts = object_path.lstrip("/").split("/")
        if len(parts) < 2:
            return None, None

        owner_type = parts[0]
        if owner_type not in OWNER_TYPE_TO_ROLE:
            return None, None

        try:
            owner_id = UUID(parts[1])
            return owner_type, owner_id
        except (ValueError, IndexError):
            return None, None

    @staticmethod
    def validate_path_access(user: User, object_path: str) -> bool:
        """
        Validate user can access the given object path.

        This method is used for MinIO path validation (Task 8).
        Raises PermissionDeniedException if access denied (AC: #7).

        Args:
            user: The authenticated user
            object_path: Full path to the object (e.g., "/publishers/123/file.pdf")

        Returns:
            True if access is allowed

        Raises:
            PermissionDeniedException: If user cannot access the path
        """
        # Admin/Supervisor bypass
        if user.role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
            return True

        # Parse the path to get owner info
        owner_type, owner_id = AuthorizationService.parse_path_ownership(object_path)

        if owner_type is None or owner_id is None:
            # Invalid path format - deny access
            raise PermissionDeniedException(
                user_id=user.id,
                resource_type="storage_path",
                resource_id=None,
                action="access",
                reason=f"Invalid storage path format: {object_path}",
            )

        # Validate ownership
        if not AuthorizationService.validate_resource_ownership(
            user, owner_id, owner_type
        ):
            raise PermissionDeniedException(
                user_id=user.id,
                resource_type="storage_path",
                resource_id=owner_id,
                action="access",
                reason=f"User does not own {owner_type}/{owner_id}",
            )

        return True
