"""Migrate config_json from TEXT to JSONB for queryability

Existing rows contain valid JSON written by json.dumps, but may be NULL or
empty string. The USING clause handles those gracefully; invalid JSON would
fail the migration and surface for manual inspection (should not happen).

Revision ID: 020
Revises: 019
Create Date: 2026-09-03
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = '020'
down_revision: Union[str, None] = '019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TEXT -> JSONB with safe cast for NULL/empty. Existing valid JSON strings become JSONB objects.
    # Using NULLIF handles empty string -> NULL -> NULL::jsonb = NULL.
    # Invalid JSON would raise and abort migration for manual review (not silently lost).
    op.execute(
        """
        ALTER TABLE scheduled_reports
        ALTER COLUMN config_json TYPE JSONB
        USING (NULLIF(config_json, '')::jsonb)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE scheduled_reports
        ALTER COLUMN config_json TYPE TEXT
        USING (config_json::text)
        """
    )
