"""Add owner view and download tracking to reports

Revision ID: 022
Revises: 021
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '022'
down_revision: Union[str, None] = '021'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('owner_view_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('reports', sa.Column('owner_last_viewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('reports', sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('reports', sa.Column('last_downloaded_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'last_downloaded_at')
    op.drop_column('reports', 'download_count')
    op.drop_column('reports', 'owner_last_viewed_at')
    op.drop_column('reports', 'owner_view_count')
