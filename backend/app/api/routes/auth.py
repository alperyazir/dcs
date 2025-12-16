"""
Authentication API Routes.

Provides endpoints for:
- POST /login - User login with email/password (AC: #1, #2, #3, #4)
- POST /refresh - Token refresh (AC: #7)

Implements rate limiting (AC: #8) and audit logging (AC: #9).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.middleware.rate_limit import limiter
from app.models import RefreshTokenRequest, TokenResponse
from app.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserInactiveError,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def get_auth_service(session: SessionDep) -> AuthService:
    """Dependency to get AuthService instance."""
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling X-Forwarded-For."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """
    OAuth2 compatible login endpoint.

    Accepts email/password and returns access + refresh tokens.

    **Rate Limited:** 5 attempts per minute per IP (AC: #8)

    - **username**: User's email address
    - **password**: User's password

    Returns:
        TokenResponse with access_token, refresh_token, token_type, expires_in

    Raises:
        - 401: Invalid credentials or inactive account
        - 429: Too many requests (rate limit exceeded)
    """
    client_ip = get_client_ip(request)

    try:
        tokens = auth_service.authenticate(
            email=form_data.username,  # OAuth2 spec uses 'username' field for email
            password=form_data.password,
        )
        logger.info(
            "User logged in successfully",
            extra={
                "email": form_data.username,
                "client_ip": client_ip,
                "event": "login_success",
            },
        )
        return tokens

    except UserInactiveError:
        logger.warning(
            "Login attempt for inactive account",
            extra={
                "email": form_data.username,
                "client_ip": client_ip,
                "event": "login_inactive_user",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except InvalidCredentialsError:
        logger.warning(
            "Failed login attempt",
            extra={
                "email_attempted": form_data.username,
                "client_ip": client_ip,
                "event": "login_failed",
            },
        )
        # Generic message to prevent user enumeration (AC: #2, #3)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Implements token rotation - new refresh token is issued with each refresh (AC: #7).

    - **refresh_token**: Valid refresh token from previous login

    Returns:
        TokenResponse with new access_token and refresh_token

    Raises:
        - 401: Invalid or expired refresh token
    """
    client_ip = get_client_ip(request)

    try:
        tokens = auth_service.refresh_tokens(body.refresh_token)
        logger.info(
            "Token refreshed successfully",
            extra={
                "client_ip": client_ip,
                "event": "token_refresh_success",
            },
        )
        return tokens

    except InvalidRefreshTokenError:
        logger.warning(
            "Invalid refresh token attempt",
            extra={
                "client_ip": client_ip,
                "event": "token_refresh_failed",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
