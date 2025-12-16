"""
Tenant Context Manager for Multi-Tenant Database Isolation (Story 2.3, Task 1).

Provides request-scoped tenant context using Python's contextvars.
This context is used by:
- TenantAwareRepository for automatic tenant filtering
- Database session injection for PostgreSQL RLS

References:
- AC: #1 (middleware injects tenant_id into session context)
- AC: #9 (tenant_id from request.state used for filtering)
"""

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    """
    Immutable tenant context for request-scoped data.

    Attributes:
        user_id: UUID of the authenticated user
        tenant_id: UUID of the user's tenant (None for system operations)
        bypass_filter: True for Admin/Supervisor to bypass tenant filtering (AC: #4)
    """

    user_id: UUID | None = None
    tenant_id: UUID | None = None
    bypass_filter: bool = False


# Context variable for request-scoped tenant context
# Default is empty TenantContext (no filtering until explicitly set)
_tenant_context: ContextVar[TenantContext] = ContextVar(
    "tenant_context", default=TenantContext()
)


def get_tenant_context() -> TenantContext:
    """
    Get the current tenant context.

    Returns:
        TenantContext: Current request's tenant context, or default if not set.

    Usage:
        ctx = get_tenant_context()
        if ctx.bypass_filter:
            # Skip tenant filtering for Admin/Supervisor
        elif ctx.tenant_id:
            # Apply tenant_id filter
    """
    return _tenant_context.get()


def set_tenant_context(
    user_id: UUID | None,
    tenant_id: UUID | None,
    bypass: bool = False,
) -> None:
    """
    Set the tenant context for the current request.

    Called by TenantContextMiddleware after extracting JWT claims.
    Creates a new immutable TenantContext and stores it in the context variable.

    Args:
        user_id: UUID of authenticated user (from JWT sub claim)
        tenant_id: UUID of user's tenant (from JWT tenant_id claim)
        bypass: True for Admin/Supervisor to bypass tenant filtering (AC: #4)

    Example:
        # In middleware after JWT validation:
        set_tenant_context(
            user_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tenant_id"]),
            bypass=(role in ["admin", "supervisor"])
        )
    """
    ctx = TenantContext(user_id=user_id, tenant_id=tenant_id, bypass_filter=bypass)
    _tenant_context.set(ctx)


def clear_tenant_context() -> None:
    """
    Clear the tenant context, resetting to default.

    Called at the end of request processing to prevent context leakage
    between requests in async environments.

    Example:
        # In middleware after response:
        try:
            response = await call_next(request)
            return response
        finally:
            clear_tenant_context()
    """
    _tenant_context.set(TenantContext())
