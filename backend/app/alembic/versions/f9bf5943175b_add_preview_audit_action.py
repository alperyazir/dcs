"""Add PREVIEW to AuditAction enum

Story 4.3: Implement Asset Preview Endpoints
Adds PREVIEW audit action for tracking preview URL generation.

Revision ID: f9bf5943175b
Revises: e9e33f46df05
Create Date: 2025-12-18 01:19:50.754176
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f9bf5943175b"
down_revision = "e9e33f46df05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add PREVIEW value to auditaction enum (Story 4.3, Task 5.2)."""
    # Add new value to the auditaction enum (PostgreSQL)
    # Must use raw SQL for enum modification
    # Note: Value uses lowercase to match Python enum .value
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'preview'")


def downgrade() -> None:
    """PostgreSQL doesn't support removing enum values directly.

    To downgrade, you would need to recreate the enum without this value
    and update all existing data. This is intentionally left as a no-op
    since removing enum values requires complex migrations.
    """
    pass
