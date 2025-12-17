from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# RS256 algorithm for asymmetric JWT signing (AC: #10)
ALGORITHM = "RS256"


def create_access_token(
    user_id: UUID,
    email: str,
    role: str,
    tenant_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create JWT access token with RS256 signing.

    Token payload includes: sub (user_id), email, role, tenant_id, exp, iat (AC: #9)
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "tenant_id": str(tenant_id),
        "exp": expire,
        "iat": now,
        "type": "access",
        "jti": str(uuid4()),  # Unique token ID for rotation support
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_PRIVATE_KEY.get_secret_value(),
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create JWT refresh token with RS256 signing (AC: #7).

    Refresh tokens have longer expiry (7 days) and minimal payload.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "jti": str(uuid4()),  # Unique token ID for rotation support
    }

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_PRIVATE_KEY.get_secret_value(),
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT token using RS256 public key.

    Returns the decoded payload if valid.
    Raises jwt.InvalidTokenError for invalid/expired tokens.
    """
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.JWT_PUBLIC_KEY,
        algorithms=[ALGORITHM],
    )
    return payload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password using bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)
