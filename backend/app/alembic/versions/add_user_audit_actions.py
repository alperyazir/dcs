"""Add user management audit actions to AuditAction enum

Story 2.5: Implement User Management Endpoints for Admin/Supervisor
Adds USER_CREATE, USER_UPDATE, USER_DELETE to the auditaction PostgreSQL enum.

Revision ID: add_user_audit_actions
Revises: c_rls_policies_and_indexes
Create Date: 2025-12-17
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_user_audit_actions"
down_revision = "c_rls_policies_and_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new values to the auditaction enum (PostgreSQL)
    # Must use raw SQL for enum modification
    # Note: Values use lowercase to match existing enum pattern (upload, download, etc.)
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'user_create'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'user_update'")
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'user_delete'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # To downgrade, you would need to recreate the enum without these values
    # and update all existing data. This is intentionally left as a no-op
    # since removing enum values requires complex migrations.
    pass
