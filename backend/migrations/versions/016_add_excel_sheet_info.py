"""Add excel_sheet_info for multi-sheet Excel warning

Revision ID: 016
Revises: 015
Create Date: 2026-08-23

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '016'
down_revision: Union[str, None] = '015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # uploads: store sheet info at upload time for immediate feedback
    op.execute(
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS excel_sheet_info JSONB;"
    )
    # reports: copy from upload for persistent report view
    op.execute(
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS excel_sheet_info JSONB;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE uploads DROP COLUMN IF EXISTS excel_sheet_info;")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS excel_sheet_info;")
