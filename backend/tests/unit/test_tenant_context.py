"""
Unit tests for Tenant Context Manager (Story 2.3, Task 1).

Tests:
- TenantContext dataclass creation
- Context variable get/set operations
- Bypass filter flag behavior
- Thread-safety of context variables

References:
- AC: #1 (middleware injects tenant_id into session context)
- AC: #9 (tenant_id from request.state used for filtering)
"""

from uuid import uuid4

import pytest

from app.core.tenant_context import (
    TenantContext,
    clear_tenant_context,
    get_tenant_context,
    set_tenant_context,
)


class TestTenantContext:
    """Tests for TenantContext dataclass."""

    def test_create_tenant_context_with_defaults(self):
        """TenantContext should have None defaults and bypass_filter=False."""
        ctx = TenantContext()
        assert ctx.user_id is None
        assert ctx.tenant_id is None
        assert ctx.bypass_filter is False

    def test_create_tenant_context_with_values(self):
        """TenantContext should store provided values."""
        user_id = uuid4()
        tenant_id = uuid4()
        ctx = TenantContext(user_id=user_id, tenant_id=tenant_id, bypass_filter=True)

        assert ctx.user_id == user_id
        assert ctx.tenant_id == tenant_id
        assert ctx.bypass_filter is True

    def test_tenant_context_immutable_by_default(self):
        """TenantContext should be a frozen dataclass."""
        ctx = TenantContext()
        with pytest.raises(AttributeError):
            ctx.user_id = uuid4()  # type: ignore


class TestContextVariableOperations:
    """Tests for context variable get/set/clear operations."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_get_tenant_context_returns_default(self):
        """get_tenant_context should return default TenantContext when not set."""
        ctx = get_tenant_context()
        assert isinstance(ctx, TenantContext)
        assert ctx.user_id is None
        assert ctx.tenant_id is None
        assert ctx.bypass_filter is False

    def test_set_tenant_context_stores_values(self):
        """set_tenant_context should store values retrievable by get_tenant_context."""
        user_id = uuid4()
        tenant_id = uuid4()

        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        ctx = get_tenant_context()
        assert ctx.user_id == user_id
        assert ctx.tenant_id == tenant_id
        assert ctx.bypass_filter is False

    def test_set_tenant_context_with_bypass(self):
        """set_tenant_context with bypass=True should set bypass_filter=True."""
        user_id = uuid4()
        tenant_id = uuid4()

        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=True)

        ctx = get_tenant_context()
        assert ctx.bypass_filter is True

    def test_clear_tenant_context_resets_to_default(self):
        """clear_tenant_context should reset to default values."""
        user_id = uuid4()
        tenant_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=True)

        clear_tenant_context()

        ctx = get_tenant_context()
        assert ctx.user_id is None
        assert ctx.tenant_id is None
        assert ctx.bypass_filter is False

    def test_set_tenant_context_with_none_tenant_id(self):
        """set_tenant_context should accept None tenant_id (for system operations)."""
        user_id = uuid4()

        set_tenant_context(user_id=user_id, tenant_id=None, bypass=True)

        ctx = get_tenant_context()
        assert ctx.user_id == user_id
        assert ctx.tenant_id is None
        assert ctx.bypass_filter is True


class TestBypassFilterBehavior:
    """Tests for bypass_filter flag behavior for Admin/Supervisor."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_admin_user_has_bypass_true(self):
        """Admin user context should have bypass_filter=True."""
        admin_id = uuid4()
        tenant_id = uuid4()

        # Simulate middleware setting for admin
        set_tenant_context(user_id=admin_id, tenant_id=tenant_id, bypass=True)

        ctx = get_tenant_context()
        assert ctx.bypass_filter is True

    def test_regular_user_has_bypass_false(self):
        """Regular user context should have bypass_filter=False."""
        user_id = uuid4()
        tenant_id = uuid4()

        # Simulate middleware setting for regular user
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        ctx = get_tenant_context()
        assert ctx.bypass_filter is False

    def test_bypass_filter_cannot_be_changed_after_set(self):
        """Once context is set, bypass_filter cannot be modified (frozen dataclass)."""
        user_id = uuid4()
        tenant_id = uuid4()
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=False)

        ctx = get_tenant_context()
        with pytest.raises(AttributeError):
            ctx.bypass_filter = True  # type: ignore


class TestTenantContextIntegration:
    """Tests for tenant context integration with request.state (AC: #9)."""

    def setup_method(self):
        """Clear context before each test."""
        clear_tenant_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_tenant_context()

    def test_context_from_request_state_regular_user(self):
        """Context should be set from request.state for regular user."""
        # Simulate what middleware sets on request.state
        user_id = uuid4()
        tenant_id = uuid4()
        bypass = False

        # This is called by middleware after reading request.state
        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=bypass)

        ctx = get_tenant_context()
        assert ctx.user_id == user_id
        assert ctx.tenant_id == tenant_id
        assert ctx.bypass_filter is False

    def test_context_from_request_state_admin_user(self):
        """Context should have bypass=True for admin from request.state."""
        user_id = uuid4()
        tenant_id = uuid4()
        bypass = True  # Admin has bypass_tenant_filter=True in request.state

        set_tenant_context(user_id=user_id, tenant_id=tenant_id, bypass=bypass)

        ctx = get_tenant_context()
        assert ctx.bypass_filter is True
