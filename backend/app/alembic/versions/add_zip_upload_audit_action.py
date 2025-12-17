"""Add ZIP upload audit action to AuditAction enum

Story 3.3: Implement ZIP Archive Upload with Streaming Extraction
Adds ASSET_ZIP_UPLOAD to the auditaction PostgreSQL enum.

Revision ID: add_zip_upload_audit_action
Revises: add_signed_url_audit_actions
Create Date: 2025-12-17
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_zip_upload_audit_action"
down_revision = "add_signed_url_audit_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new values to the auditaction enum (PostgreSQL)
    # Must use raw SQL for enum modification
    # Note: Add both lowercase (Python enum .value) and uppercase (Python enum .name)
    # SQLModel may use either depending on configuration
    op.execute(
        "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'asset_zip_upload'"
    )
    op.execute(
        "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'ASSET_ZIP_UPLOAD'"
    )


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # To downgrade, you would need to recreate the enum without these values
    # and update all existing data. This is intentionally left as a no-op
    # since removing enum values requires complex migrations.
    pass
