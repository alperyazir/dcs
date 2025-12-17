import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import col, delete, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
)
from app.api.deps_auth import require_supervisor_or_above
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.middleware.rate_limit import get_client_ip, get_dynamic_rate_limit, limiter
from app.models import (
    AuditAction,
    AuditLogCreate,
    Item,
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UserRole,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services.authorization_service import has_role_or_higher
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(require_supervisor_or_above)],
    response_model=UsersPublic,
)
@limiter.limit(get_dynamic_rate_limit)
def read_users(
    request: Request,  # noqa: ARG001 - Required by rate limiter
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

    Requires Admin or Supervisor role (Story 2.5, AC: #6, #7).
    Rate limited based on user role - Admins/Supervisors have unlimited access (Story 2.4).
    """
    # Build dynamic query with filters (Story 2.5, Task 2)
    statement = select(User)

    if role:
        statement = statement.where(User.role == role)

    if tenant_id:
        statement = statement.where(User.tenant_id == tenant_id)

    # Get count for pagination (with filters applied)
    count_statement = select(func.count()).select_from(statement.subquery())
    count = session.exec(count_statement).one()

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersPublic(data=users, count=count)


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
    Rate limited based on user role - Admins/Supervisors have unlimited access (Story 2.4).
    Logs user creation in audit_logs (Story 2.5, AC: #10).
    """
    # Validate tenant exists if provided (Story 2.5, AC: #2)
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
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)

    # Create audit log for user creation (Story 2.5, AC: #10)
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

    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
@limiter.limit(get_dynamic_rate_limit)
def update_user_me(
    request: Request,  # noqa: ARG001 - Required by rate limiter
    *,
    session: SessionDep,
    user_in: UserUpdateMe,
    current_user: CurrentUser,
) -> Any:
    """
    Update own user.

    Rate limited based on user role (Story 2.4).
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
@limiter.limit(get_dynamic_rate_limit)
def update_password_me(
    request: Request,  # noqa: ARG001 - Required by rate limiter
    *,
    session: SessionDep,
    body: UpdatePassword,
    current_user: CurrentUser,
) -> Any:
    """
    Update own password.

    Rate limited based on user role (Story 2.4).
    """
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
@limiter.limit(get_dynamic_rate_limit)
def read_user_me(
    request: Request,  # noqa: ARG001 - Required by rate limiter
    current_user: CurrentUser,
) -> Any:
    """
    Get current user.

    Rate limited based on user role (Story 2.4).
    """
    return current_user


@router.delete("/me", response_model=Message)
@limiter.limit(get_dynamic_rate_limit)
def delete_user_me(
    request: Request,  # noqa: ARG001 - Required by rate limiter
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Delete own user.

    Rate limited based on user role (Story 2.4).
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


def get_signup_rate_limit() -> str:
    """
    Get configurable signup rate limit (Story 2.4).

    Returns rate limit string for public signup endpoint.
    Configurable via RATE_LIMIT_SIGNUP environment variable.
    Default: 10/minute to prevent signup abuse.
    """
    return settings.RATE_LIMIT_SIGNUP


@router.post("/signup", response_model=UserPublic)
@limiter.limit(get_signup_rate_limit)
def register_user(
    request: Request,  # noqa: ARG001 - Required by rate limiter
    session: SessionDep,
    user_in: UserRegister,
) -> Any:
    """
    Create new user without the need to be logged in.

    Rate limited by IP to prevent abuse (configurable via RATE_LIMIT_SIGNUP).
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get("/{user_id}", response_model=UserPublic)
@limiter.limit(get_dynamic_rate_limit)
def read_user_by_id(
    request: Request,  # noqa: ARG001 - Required by rate limiter
    user_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get a specific user by id.

    Returns user details including role, tenant_id, created_at, updated_at.
    Rate limited based on user role (Story 2.4).
    Admins and Supervisors can view any user (Story 2.5, AC: #4).
    """
    user = session.get(User, user_id)

    # Handle not found (Story 2.5, Task 3.3)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": f"User with ID {user_id} does not exist",
                "details": {"user_id": str(user_id)},
            },
        )

    # Allow viewing own profile
    if user == current_user:
        return user

    # Allow Admin/Supervisor to view any user (Story 2.5, AC: #4)
    if has_role_or_higher(current_user.role, UserRole.SUPERVISOR):
        return user

    # Backward compatibility: superuser flag
    if current_user.is_superuser:
        return user

    raise HTTPException(
        status_code=403,
        detail="The user doesn't have enough privileges",
    )


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

    Requires Admin or Supervisor role (Story 2.5, AC: #5).
    Rate limited based on user role - Admins/Supervisors have unlimited access (Story 2.4).
    Logs changes in audit_logs (Story 2.5, AC: #10).
    """
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )

    # Capture changes for audit log before update
    changes = {}
    update_data = user_in.model_dump(exclude_unset=True)
    for field, new_value in update_data.items():
        if field == "password":
            # Don't log actual password values
            changes[field] = {"old": "[REDACTED]", "new": "[REDACTED]"}
        else:
            old_value = getattr(db_user, field, None)
            # Convert enums to their values for comparison
            if old_value is not None and hasattr(old_value, "value"):
                old_value = old_value.value
            if new_value is not None and hasattr(new_value, "value"):
                new_value = new_value.value
            if str(old_value) != str(new_value):
                changes[field] = {"old": str(old_value), "new": str(new_value)}

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)

    # Create audit log for user update (Story 2.5, AC: #10)
    if changes:  # Only log if there were actual changes
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


@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_supervisor_or_above)],
)
@limiter.limit(get_dynamic_rate_limit)
def delete_user(
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
) -> Message:
    """
    Delete a user.

    Requires Admin or Supervisor role (Story 2.5, AC: #8).
    Rate limited based on user role - Admins/Supervisors have unlimited access (Story 2.4).
    Logs deletion in audit_logs (Story 2.5, AC: #10).
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )

    # Capture user info before deletion for audit log
    deleted_user_info = {
        "target_user_id": str(user.id),
        "target_email": user.email,
        "target_role": user.role.value,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
    }

    statement = delete(Item).where(col(Item.owner_id) == user_id)
    session.exec(statement)  # type: ignore
    session.delete(user)

    # Create audit log for user deletion (Story 2.5, AC: #10)
    crud.create_audit_log(
        session=session,
        audit_log_in=AuditLogCreate(
            action=AuditAction.USER_DELETE,
            user_id=current_user.id,
            ip_address=get_client_ip(request),
            metadata_json=deleted_user_info,
        ),
    )

    session.commit()
    return Message(message="User deleted successfully")
