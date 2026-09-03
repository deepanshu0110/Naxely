"""Add consecutive_failures and last_error to scheduled_reports

For failure retry policy: advance next_run_at on failure, track consecutive
failures, auto-disable after 3, and surface last_error for debugging.

Revision ID: 019
Revises: 018
Create Date: 2026-09-02
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '019'
down_revision: Union[str, None] = '018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scheduled_reports', sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('scheduled_reports', sa.Column('last_error', sa.Text(), nullable=True))
    op.create_index('idx_scheduled_reports_consecutive_failures', 'scheduled_reports', ['consecutive_failures'])


def downgrade() -> None:
    op.drop_index('idx_scheduled_reports_consecutive_failures', table_name='scheduled_reports')
    op.drop_column('scheduled_reports', 'consecutive_failures')
    op.drop_column('scheduled_reports', 'last_error')
