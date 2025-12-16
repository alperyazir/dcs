"""
Repository layer for Dream Central Storage.

Provides:
- TenantAwareRepository: Base repository with automatic tenant filtering
- AssetRepository: Asset-specific data access (Story 2.3, Task 4)
"""

from app.repositories.asset_repository import AssetRepository
from app.repositories.base import TenantAwareRepository

__all__ = ["TenantAwareRepository", "AssetRepository"]
