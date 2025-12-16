"""Add Row-Level Security policies and performance indexes

Revision ID: c_rls_policies_and_indexes
Revises: b198e225ee29
Create Date: 2025-12-16

Story 2.3: Multi-Tenant Database Isolation with Row-Level Security
- Task 5: Create PostgreSQL RLS policies
- Task 6: Session parameter injection support
- Task 7: Performance indexes
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "c_rls_policies_and_indexes"
down_revision = "b198e225ee29"
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade database with RLS policies and indexes.

    RLS Design (Defense-in-Depth):
    - Primary filtering happens at Python application layer (TenantAwareRepository)
    - RLS serves as BACKSTOP defense for direct database access
    - Empty/NULL app.current_tenant_id bypasses RLS (for Admin/Supervisor)
    """

    # ==========================================================================
    # Task 5: Row-Level Security Policies
    # ==========================================================================

    # Enable RLS on asset table (Task 5.2)
    op.execute("ALTER TABLE asset ENABLE ROW LEVEL SECURITY")

    # Force RLS even for table owner (important for security)
    op.execute("ALTER TABLE asset FORCE ROW LEVEL SECURITY")

    # Policy for SELECT (Task 5.3)
    # Allow if: tenant_id matches session parameter OR session parameter is empty (bypass)
    op.execute(
        """
        CREATE POLICY tenant_isolation_select ON asset
        FOR SELECT
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '') = ''
        )
        """
    )

    # Policy for INSERT (Task 5.4)
    op.execute(
        """
        CREATE POLICY tenant_isolation_insert ON asset
        FOR INSERT
        WITH CHECK (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '') = ''
        )
        """
    )

    # Policy for UPDATE (Task 5.5)
    op.execute(
        """
        CREATE POLICY tenant_isolation_update ON asset
        FOR UPDATE
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '') = ''
        )
        """
    )

    # Policy for DELETE (Task 5.6)
    op.execute(
        """
        CREATE POLICY tenant_isolation_delete ON asset
        FOR DELETE
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
            OR COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '') = ''
        )
        """
    )

    # ==========================================================================
    # Task 7: Performance Indexes
    # ==========================================================================

    # Composite index for tenant + user queries (Task 7.3)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_assets_tenant_user ON asset(tenant_id, user_id)"
    )

    # Partial index for non-deleted assets (Task 7.5)
    # This optimizes the most common query pattern: listing active assets
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_assets_tenant_active
        ON asset(tenant_id, created_at DESC)
        WHERE is_deleted = false
        """
    )

    # ==========================================================================
    # Documentation Comment (Task 5.8)
    # ==========================================================================
    op.execute(
        """
        COMMENT ON TABLE asset IS
        'Asset storage with Row-Level Security (RLS) enabled.
        RLS policies enforce tenant isolation as a BACKSTOP defense layer.
        Primary filtering happens at Python application layer (TenantAwareRepository).
        Set session parameter: SET LOCAL app.current_tenant_id = ''tenant-uuid'';
        Empty string bypasses RLS (for Admin/Supervisor operations).
        Story 2.3: Multi-Tenant Database Isolation.'
        """
    )


def downgrade():
    """Remove RLS policies and custom indexes."""

    # Remove indexes
    op.execute("DROP INDEX IF EXISTS idx_assets_tenant_active")
    op.execute("DROP INDEX IF EXISTS idx_assets_tenant_user")

    # Remove RLS policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_delete ON asset")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_update ON asset")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_insert ON asset")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_select ON asset")

    # Disable RLS
    op.execute("ALTER TABLE asset NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE asset DISABLE ROW LEVEL SECURITY")

    # Remove comment
    op.execute("COMMENT ON TABLE asset IS NULL")
