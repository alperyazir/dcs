"""Add ASSET_UPLOAD to auditaction enum

Revision ID: d93a7c0df933
Revises: add_user_audit_actions
Create Date: 2025-12-17 18:53:00.900257

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'd93a7c0df933'
down_revision = 'add_user_audit_actions'
branch_labels = None
depends_on = None


def upgrade():
    # Add new enum value for asset upload action (Story 3.1)
    # Using uppercase name to match existing enum values pattern (UPLOAD, DOWNLOAD, etc.)
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'ASSET_UPLOAD'")


def downgrade():
    # PostgreSQL doesn't support removing enum values directly
    # The value will remain but be unused if this migration is reversed
    pass
