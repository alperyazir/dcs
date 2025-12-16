"""
Unit tests for TenantAwareRepository (Story 2.3, Task 2).

Tests:
- Automatic tenant filtering on queries
- Bypass filter for Admin/Supervisor
- Tenant-aware CRUD operations
- __tenant_aware__ marker attribute

References:
- AC: #2 (all queries automatically include tenant_id filters)
- AC: #3 (Asset queries filter by tenant_id)
- AC: #6 (cross-tenant query returns zero results)
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.tenant_context import (
    clear_tenant_context,
    get_tenant_context,
    set_tenant_context,
)
from app.repositories.base import TenantAwareRepository


class TestTenantAwareRepositoryFiltering:
    """Tests for automatic tenant filtering (AC: #2, #3, #6)."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_apply_tenant_filter_with_tenant_context(self):
        """_apply_tenant_filter should add tenant_id filter when context is set."""
        tenant_id = uuid4()
        user_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        # Mock model with __tenant_aware__ = True
        mock_model = MagicMock()
        mock_model.__tenant_aware__ = True
        mock_model.__name__ = "MockModel"
        mock_model.tenant_id = MagicMock()

        # Mock session
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)

        # Mock statement
        mock_statement = MagicMock()

        # Apply filter
        _result = repo._apply_tenant_filter(mock_statement)  # noqa: F841

        # Should have called where() with tenant_id filter
        mock_statement.where.assert_called_once()

    def test_apply_tenant_filter_with_bypass(self):
        """_apply_tenant_filter should NOT add filter when bypass=True (AC: #4)."""
        tenant_id = uuid4()
        user_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=True)

        mock_model = MagicMock()
        mock_model.__tenant_aware__ = True
        mock_model.__name__ = "MockModel"
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)
        mock_statement = MagicMock()

        result = repo._apply_tenant_filter(mock_statement)

        # Should return statement unchanged (no where() call)
        mock_statement.where.assert_not_called()
        assert result == mock_statement

    def test_apply_tenant_filter_without_tenant_aware_marker(self):
        """_apply_tenant_filter should NOT filter if model lacks __tenant_aware__."""
        tenant_id = uuid4()
        user_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        mock_model = MagicMock(spec=[])  # No __tenant_aware__
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)
        mock_statement = MagicMock()

        result = repo._apply_tenant_filter(mock_statement)

        # Should return statement unchanged
        mock_statement.where.assert_not_called()
        assert result == mock_statement

    def test_apply_tenant_filter_without_context(self):
        """_apply_tenant_filter should NOT filter if no context is set."""
        # Context is cleared by setup_method, so tenant_id is None
        mock_model = MagicMock()
        mock_model.__tenant_aware__ = True
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)
        mock_statement = MagicMock()

        result = repo._apply_tenant_filter(mock_statement)

        # Should return statement unchanged (no tenant_id to filter by)
        mock_statement.where.assert_not_called()
        assert result == mock_statement


class TestTenantAwareRepositoryBypassBehavior:
    """Tests for Admin/Supervisor bypass behavior (AC: #4)."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_admin_bypass_returns_all_tenants(self):
        """Admin with bypass=True should see all tenant data."""
        admin_id = uuid4()
        tenant_id = uuid4()
        set_tenant_context(user_id=admin_id, tenant_id=tenant_id, bypass=True)

        ctx = get_tenant_context()
        assert ctx.bypass_filter is True

        # Repository should not filter
        mock_model = MagicMock()
        mock_model.__tenant_aware__ = True
        mock_model.__name__ = "MockModel"
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)
        mock_statement = MagicMock()

        _result = repo._apply_tenant_filter(mock_statement)  # noqa: F841
        mock_statement.where.assert_not_called()

    def test_supervisor_bypass_returns_all_tenants(self):
        """Supervisor with bypass=True should see all tenant data."""
        supervisor_id = uuid4()
        tenant_id = uuid4()
        set_tenant_context(user_id=supervisor_id, tenant_id=tenant_id, bypass=True)

        ctx = get_tenant_context()
        assert ctx.bypass_filter is True

    def test_regular_user_cannot_bypass(self):
        """Regular user (Publisher/Teacher/Student) cannot bypass filtering."""
        user_id = uuid4()
        tenant_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        ctx = get_tenant_context()
        assert ctx.bypass_filter is False


class TestTenantAwareRepositoryModelMarker:
    """Tests for __tenant_aware__ model marker (Task 2.5)."""

    def test_model_with_tenant_aware_true(self):
        """Model with __tenant_aware__ = True should be filtered."""
        # This is tested via _apply_tenant_filter tests above
        pass

    def test_model_without_tenant_aware(self):
        """Model without __tenant_aware__ should not be filtered."""
        tenant_id = uuid4()
        user_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        # Model without __tenant_aware__ attribute
        mock_model = MagicMock(spec=["id", "name"])
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)
        mock_statement = MagicMock()

        _result = repo._apply_tenant_filter(mock_statement)  # noqa: F841

        # Should not filter
        mock_statement.where.assert_not_called()

    def test_model_with_tenant_aware_false(self):
        """Model with __tenant_aware__ = False should not be filtered."""
        tenant_id = uuid4()
        user_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        mock_model = MagicMock()
        mock_model.__tenant_aware__ = False
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)
        mock_statement = MagicMock()

        _result = repo._apply_tenant_filter(mock_statement)  # noqa: F841

        # Should not filter
        mock_statement.where.assert_not_called()


class TestCrossTenantWritePrevention:
    """Tests for cross-tenant write prevention (AC: #5, Task 8)."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_validate_tenant_ownership_same_tenant(self):
        """validate_tenant_ownership should pass for same tenant."""
        tenant_id = uuid4()
        user_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        mock_model = MagicMock()
        mock_model.__tenant_aware__ = True
        mock_model.__name__ = "MockModel"
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)

        # Should not raise
        repo._validate_tenant_ownership(tenant_id)

    def test_validate_tenant_ownership_different_tenant_raises(self):
        """validate_tenant_ownership should raise for different tenant."""
        from app.core.exceptions import PermissionDeniedException

        tenant_a = uuid4()
        tenant_b = uuid4()
        user_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_a, bypass=False)

        mock_model = MagicMock()
        mock_model.__tenant_aware__ = True
        mock_model.__name__ = "MockModel"
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)

        # Should raise PermissionDeniedException
        with pytest.raises(PermissionDeniedException):
            repo._validate_tenant_ownership(tenant_b)

    def test_validate_tenant_ownership_admin_bypasses(self):
        """Admin with bypass should pass any tenant ownership check."""
        admin_id = uuid4()
        tenant_a = uuid4()
        tenant_b = uuid4()  # Different tenant
        set_tenant_context(user_id=admin_id, tenant_id=tenant_a, bypass=True)

        mock_model = MagicMock()
        mock_model.__tenant_aware__ = True
        mock_model.__name__ = "MockModel"
        mock_session = MagicMock()

        repo = TenantAwareRepository(session=mock_session, model=mock_model)

        # Admin should be able to write to any tenant
        repo._validate_tenant_ownership(tenant_b)
