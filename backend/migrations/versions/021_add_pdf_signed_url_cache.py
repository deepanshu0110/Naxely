"""Add pdf_signed_url cache to reports

Revision ID: 021
Revises: 020
Create Date: 2026-09-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '021'
down_revision: Union[str, None] = '020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('pdf_signed_url', sa.Text(), nullable=True))
    op.add_column('reports', sa.Column('pdf_signed_url_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'pdf_signed_url_expires_at')
    op.drop_column('reports', 'pdf_signed_url')
