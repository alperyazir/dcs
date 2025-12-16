"""
Authorization dependencies for FastAPI routes (Story 2.2).

Provides reusable dependencies for role-based access control (Task 2):
- require_authenticated: Base authentication check
- require_admin: Admin role only
- require_supervisor_or_above: Admin or Supervisor
- require_role: Factory for specific role
- require_role_or_above: Factory for role hierarchy check

References:
- AC: #9 (403 with descriptive error)
- AC: #10 (reusable dependencies)
"""

from collections.abc import Callable

from fastapi import Depends

from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedException
from app.models import User, UserRole
from app.services.authorization_service import has_role_or_higher

# =============================================================================
# BASE AUTHENTICATION DEPENDENCY (Task 2.2)
# =============================================================================


def require_authenticated(current_user: User = Depends(get_current_user)) -> User:
    """
    Base dependency ensuring valid JWT authentication.

    Reuses existing get_current_user - no additional checks needed.
    If get_current_user passes, user is authenticated.
    """
    return current_user


# =============================================================================
# ROLE-BASED DEPENDENCIES (Task 2.3 - 2.6)
# =============================================================================


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency requiring Admin role.

    Args:
        current_user: Injected authenticated user

    Returns:
        User if admin or superuser

    Raises:
        PermissionDeniedException: If not admin/superuser (AC: #9)
    """
    # Accept both role=ADMIN and is_superuser=True for backward compatibility
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        raise PermissionDeniedException(
            user_id=current_user.id,
            resource_type="admin_endpoint",
            resource_id=None,
            action="access",
            reason=f"Admin role required, user has {current_user.role.value}",
        )
    return current_user


def require_supervisor_or_above(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency requiring Supervisor or Admin role.

    Args:
        current_user: Injected authenticated user

    Returns:
        User if supervisor or admin

    Raises:
        PermissionDeniedException: If below supervisor (AC: #9)
    """
    if not has_role_or_higher(current_user.role, UserRole.SUPERVISOR):
        raise PermissionDeniedException(
            user_id=current_user.id,
            resource_type="supervisor_endpoint",
            resource_id=None,
            action="access",
            reason="Supervisor or higher role required",
        )
    return current_user


def require_role(required_role: UserRole) -> Callable[[User], User]:
    """
    Factory function for specific role requirement.

    Args:
        required_role: The exact role required

    Returns:
        Dependency function that validates the role

    Example:
        @router.get("/publisher-only")
        def endpoint(user: User = Depends(require_role(UserRole.PUBLISHER))):
            ...
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise PermissionDeniedException(
                user_id=current_user.id,
                resource_type=f"{required_role.value}_endpoint",
                resource_id=None,
                action="access",
                reason=f"{required_role.value} role required",
            )
        return current_user

    return dependency


def require_role_or_above(minimum_role: UserRole) -> Callable[[User], User]:
    """
    Factory function for role hierarchy check.

    Args:
        minimum_role: The minimum role required in hierarchy

    Returns:
        Dependency function that validates role hierarchy

    Example:
        @router.get("/teacher-or-above")
        def endpoint(user: User = Depends(require_role_or_above(UserRole.TEACHER))):
            ...
    """

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_role_or_higher(current_user.role, minimum_role):
            raise PermissionDeniedException(
                user_id=current_user.id,
                resource_type=f"{minimum_role.value}_or_above_endpoint",
                resource_id=None,
                action="access",
                reason=f"{minimum_role.value} or higher role required",
            )
        return current_user

    return dependency
