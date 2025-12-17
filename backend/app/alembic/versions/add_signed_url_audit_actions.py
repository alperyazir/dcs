"""Add signed URL audit actions to AuditAction enum

Story 3.2: Generate Time-Limited Signed URLs for Direct MinIO Access
Adds SIGNED_URL_DOWNLOAD, SIGNED_URL_UPLOAD to the auditaction PostgreSQL enum.

Revision ID: add_signed_url_audit_actions
Revises: d93a7c0df933
Create Date: 2025-12-17
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_signed_url_audit_actions"
down_revision = "d93a7c0df933"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new values to the auditaction enum (PostgreSQL)
    # Must use raw SQL for enum modification
    # Note: Values use lowercase to match Python enum .value
    op.execute(
        "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'signed_url_download'"
    )
    op.execute(
        "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'signed_url_upload'"
    )
    op.execute(
        "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'SIGNED_URL_DOWNLOAD'"
    )
    op.execute(
        "ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'SIGNED_URL_UPLOAD'"
    )


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # To downgrade, you would need to recreate the enum without these values
    # and update all existing data. This is intentionally left as a no-op
    # since removing enum values requires complex migrations.
    pass
