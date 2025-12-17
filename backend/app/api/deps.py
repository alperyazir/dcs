"""
FastAPI Dependencies for Dream Central Storage.

Provides:
- Database session management
- JWT authentication
- Tenant context injection (Story 2.3)

References:
- AC: #1 (middleware injects tenant_id into session context)
- AC: #9 (tenant_id from request.state used for filtering)
"""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.core.tenant_context import clear_tenant_context, set_tenant_context
from app.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_tenant_session(request: Request) -> Generator[Session, None, None]:
    """
    Get database session with tenant context injected from request.state.

    This dependency:
    1. Creates a database session
    2. Sets tenant context from request.state (populated by TenantContextMiddleware)
    3. Sets PostgreSQL session parameter for RLS (Task 6)
    4. Clears tenant context on completion (prevents context leakage)

    The tenant context enables:
    - TenantAwareRepository to automatically filter by tenant_id
    - PostgreSQL RLS policies to enforce tenant isolation as backstop

    References:
        - AC: #1 (middleware injects tenant_id into session context)
        - AC: #7 (RLS policies serve as backstop defense layer)
        - AC: #9 (tenant_id from request.state used for filtering)

    Args:
        request: FastAPI Request with state populated by TenantContextMiddleware

    Yields:
        Session: SQLModel session with tenant context set
    """
    from sqlalchemy import text

    # Extract tenant context from request.state (set by TenantContextMiddleware)
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)
    bypass = getattr(request.state, "bypass_tenant_filter", False)

    # Convert string IDs to UUID if present
    user_uuid = UUID(user_id) if user_id else None
    tenant_uuid = UUID(tenant_id) if tenant_id else None

    # Set the tenant context for this request (for TenantAwareRepository)
    set_tenant_context(user_id=user_uuid, tenant_id=tenant_uuid, bypass=bypass)

    try:
        with Session(engine) as session:
            # Set PostgreSQL session parameter for RLS (Task 6)
            # Empty string bypasses RLS (for Admin/Supervisor or unauthenticated)
            if bypass or tenant_uuid is None:
                session.execute(text("SET LOCAL app.current_tenant_id = ''"))
            else:
                # Use string formatting for SET LOCAL (PostgreSQL doesn't support parameters)
                # Safe because tenant_uuid is a validated UUID object, not user input
                tenant_id_str = str(tenant_uuid)
                session.execute(
                    text(f"SET LOCAL app.current_tenant_id = '{tenant_id_str}'")
                )
            yield session
    finally:
        # Always clear context to prevent leakage between requests
        clear_tenant_context()


TenantSessionDep = Annotated[Session, Depends(get_tenant_session)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """
    Validate JWT access token and return current user.

    Uses RS256 public key for verification (AC: #5, #6, #10).
    Validates all required claims: sub, email, role, tenant_id (AC: #7.3).
    Returns 401 for expired or invalid tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=[security.ALGORITHM],
        )
        token_data = TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate all required claims (AC: #7.3)
    if not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not token_data.email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not token_data.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing role",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not token_data.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing tenant ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: not an access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
