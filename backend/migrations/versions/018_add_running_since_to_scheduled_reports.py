"""Add running_since to scheduled_reports for duplicate prevention

Prevents duplicate processing when two cron ticks overlap (>15 min batch).
Uses atomic UPDATE ... RETURNING to claim rows; running_since doubles as stale-lock recovery.

Revision ID: 018
Revises: 017
Create Date: 2026-09-02

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scheduled_reports', sa.Column('running_since', sa.DateTime(timezone=True), nullable=True))
    op.create_index('idx_scheduled_reports_running_since', 'scheduled_reports', ['running_since'])


def downgrade() -> None:
    op.drop_index('idx_scheduled_reports_running_since', table_name='scheduled_reports')
    op.drop_column('scheduled_reports', 'running_since')
