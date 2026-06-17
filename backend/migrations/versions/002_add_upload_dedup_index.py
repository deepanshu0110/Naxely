"""add partial unique index on reports for upload_id dedup

Revision ID: 002
Revises: 001
Create Date: 2026-06-17 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_active_upload
        ON reports (user_id, (config->>'upload_id'))
        WHERE status IN ('pending', 'processing') AND deleted_at IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_reports_active_upload;")
