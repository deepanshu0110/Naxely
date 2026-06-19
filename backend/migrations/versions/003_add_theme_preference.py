"""add theme_preference column to users

Revision ID: 003
Revises: 002
Create Date: 2026-06-19 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op


revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS theme_preference "
        "VARCHAR(10) DEFAULT 'light' NOT NULL;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS theme_preference;")
