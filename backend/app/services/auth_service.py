"""
Authentication Service Layer.

Handles all authentication business logic including:
- User authentication with timing-safe password verification
- Token generation (access + refresh)
- Token refresh flow
- Inactive user handling

Follows the Routes → Services → Repositories architecture pattern.
"""

import logging
from uuid import UUID

import jwt
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.models import TokenPayload, TokenResponse, User

logger = logging.getLogger(__name__)


class UserInactiveError(Exception):
    """Raised when user account is inactive."""

    pass


class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid (generic to prevent enumeration)."""

    pass


class InvalidRefreshTokenError(Exception):
    """Raised when refresh token is invalid or expired."""

    pass


class AuthService:
    """
    Authentication service implementing secure authentication flows.

    AC: #1, #2, #3, #4 - Login with timing-safe comparison
    AC: #7 - Token refresh with rotation
    """

    # Dummy hash for timing-safe comparison when user not found
    # This ensures constant-time response regardless of user existence
    _DUMMY_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.sCLYrpAhXXpKuy"

    def __init__(self, db: Session):
        self.db = db

    def authenticate(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate user and return token pair.

        Uses timing-safe password comparison to prevent user enumeration (AC: #2, #3).

        Args:
            email: User's email address
            password: User's plain text password

        Returns:
            TokenResponse with access_token, refresh_token, and metadata

        Raises:
            InvalidCredentialsError: If credentials are invalid (generic message)
            UserInactiveError: If user account is inactive (AC: #4)
        """
        # Find user by email
        statement = select(User).where(User.email == email)
        user = self.db.exec(statement).first()

        # Timing-safe: always verify password even if user not found
        # This prevents timing attacks that could enumerate valid emails
        if not user:
            verify_password(password, self._DUMMY_HASH)
            logger.warning(
                "Login failed: user not found",
                extra={"email_attempted": email, "reason": "user_not_found"},
            )
            raise InvalidCredentialsError()

        if not verify_password(password, user.hashed_password):
            logger.warning(
                "Login failed: invalid password",
                extra={"user_id": str(user.id), "reason": "invalid_password"},
            )
            raise InvalidCredentialsError()

        if not user.is_active:
            logger.warning(
                "Login failed: inactive user",
                extra={"user_id": str(user.id), "reason": "inactive_user"},
            )
            raise UserInactiveError()

        # Generate token pair
        tokens = self._create_tokens(user)

        logger.info(
            "Login successful",
            extra={"user_id": str(user.id), "email": user.email},
        )

        return tokens

    def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using valid refresh token.

        Implements token rotation for security (AC: #7).

        Args:
            refresh_token: Valid refresh token

        Returns:
            New TokenResponse with fresh access_token and refresh_token

        Raises:
            InvalidRefreshTokenError: If refresh token is invalid or expired
        """
        try:
            payload = verify_token(refresh_token)
            token_data = TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            logger.warning(
                "Token refresh failed: expired token",
                extra={"reason": "token_expired"},
            )
            raise InvalidRefreshTokenError()
        except (jwt.InvalidTokenError, Exception):
            logger.warning(
                "Token refresh failed: invalid token",
                extra={"reason": "invalid_token"},
            )
            raise InvalidRefreshTokenError()

        # Verify it's a refresh token, not an access token
        if token_data.type != "refresh":
            logger.warning(
                "Token refresh failed: wrong token type",
                extra={"token_type": token_data.type, "reason": "wrong_token_type"},
            )
            raise InvalidRefreshTokenError()

        if not token_data.sub:
            raise InvalidRefreshTokenError()

        # Get user from database
        user = self.db.get(User, UUID(token_data.sub))
        if not user:
            logger.warning(
                "Token refresh failed: user not found",
                extra={"user_id": token_data.sub, "reason": "user_not_found"},
            )
            raise InvalidRefreshTokenError()

        if not user.is_active:
            logger.warning(
                "Token refresh failed: inactive user",
                extra={"user_id": str(user.id), "reason": "inactive_user"},
            )
            raise InvalidRefreshTokenError()

        # Generate new token pair (token rotation)
        tokens = self._create_tokens(user)

        logger.info(
            "Token refresh successful",
            extra={"user_id": str(user.id)},
        )

        return tokens

    def _create_tokens(self, user: User) -> TokenResponse:
        """
        Create access and refresh token pair for user.

        Args:
            user: Authenticated User object

        Returns:
            TokenResponse with both tokens
        """
        # Handle nullable tenant_id - use user.id as fallback for single-tenant mode
        effective_tenant_id = user.tenant_id if user.tenant_id else user.id

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
            tenant_id=effective_tenant_id,
        )

        refresh_token = create_refresh_token(user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
