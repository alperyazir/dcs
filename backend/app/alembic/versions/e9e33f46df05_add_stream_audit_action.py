"""Add STREAM to AuditAction enum

Story 4.2: Implement Video and Audio Streaming with HTTP Range Support
Adds STREAM audit action for tracking streaming URL generation.

Revision ID: e9e33f46df05
Revises: add_signed_url_audit_actions
Create Date: 2025-12-18 00:51:06.603472
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e9e33f46df05"
down_revision = "add_signed_url_audit_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add STREAM value to auditaction enum (Story 4.2, Task 4.2)."""
    # Add new value to the auditaction enum (PostgreSQL)
    # Must use raw SQL for enum modification
    # Note: Value uses lowercase to match Python enum .value
    op.execute("ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'stream'")


def downgrade() -> None:
    """PostgreSQL doesn't support removing enum values directly.

    To downgrade, you would need to recreate the enum without this value
    and update all existing data. This is intentionally left as a no-op
    since removing enum values requires complex migrations.
    """
    pass
