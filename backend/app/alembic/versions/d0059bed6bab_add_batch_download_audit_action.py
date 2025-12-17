"""Add BATCH_DOWNLOAD to AuditAction enum

Story 4.4: Implement Batch Download for Multiple Assets
Adds BATCH_DOWNLOAD audit action for tracking batch download operations.

Revision ID: d0059bed6bab
Revises: f9bf5943175b
Create Date: 2025-12-18 01:33:37.451160
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d0059bed6bab"
down_revision = "f9bf5943175b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add BATCH_DOWNLOAD value to auditaction enum (Story 4.4, Task 6.2)."""
    # Add new value to the auditaction enum (PostgreSQL)
    # Must use raw SQL for enum modification
    # Note: Value uses lowercase to match Python enum .value
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'batch_download'")


def downgrade() -> None:
    """PostgreSQL doesn't support removing enum values directly.

    To downgrade, you would need to recreate the enum without this value
    and update all existing data. This is intentionally left as a no-op
    since removing enum values requires complex migrations.
    """
    pass
