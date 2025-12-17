from fastapi import APIRouter

from app.api.routes import (
    auth,
    batch_download,
    download,
    items,
    login,
    preview,
    private,
    signed_urls,
    streaming,
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
api_router.include_router(download.router)  # Story 4.1: Asset download endpoint
api_router.include_router(streaming.router)  # Story 4.2: Asset streaming endpoint
api_router.include_router(preview.router)  # Story 4.3: Asset preview endpoint
api_router.include_router(batch_download.router)  # Story 4.4: Batch download endpoint


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
