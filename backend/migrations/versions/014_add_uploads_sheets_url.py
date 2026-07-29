"""Add sheets_url to uploads and data_source_stale to reports

Revision ID: 014
Revises: 013
Create Date: 2026-07-29

"""

from typing import Sequence, Union
from alembic import op


revision: str = '014'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE uploads ADD COLUMN IF NOT EXISTS sheets_url TEXT;"
    )
    op.execute(
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS data_source_stale "
        "BOOLEAN NOT NULL DEFAULT FALSE;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE uploads DROP COLUMN IF EXISTS sheets_url;")
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS data_source_stale;")
