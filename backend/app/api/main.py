from fastapi import APIRouter

from app.api.routes import (
    auth,
    items,
    login,
    private,
    signed_urls,
    upload,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(auth.router)  # New auth endpoints: /auth/login, /auth/refresh
api_router.include_router(login.router)  # Legacy login endpoint: /login/access-token
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(upload.router)  # Story 3.1: Asset upload endpoint
api_router.include_router(signed_urls.router)  # Story 3.2: Signed URL endpoints


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
