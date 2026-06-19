"""add current_step column to reports

Revision ID: 004
Revises: 003
Create Date: 2026-06-19 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op


revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE reports ADD COLUMN IF NOT EXISTS current_step "
        "VARCHAR(50);"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE reports DROP COLUMN IF EXISTS current_step;")
