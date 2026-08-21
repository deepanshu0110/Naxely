"""Add lifecycle email automation: onboarding_completed_at, email_log, email_suppressed, pg_cron

Revision ID: 015
Revises: 014
Create Date: 2026-08-21

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '015'
down_revision: Union[str, None] = '014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users: track when onboarding was completed
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ;"
    )
    # suppression flag
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_suppressed BOOLEAN DEFAULT FALSE;"
    )
    # email_log: prevent duplicate lifecycle sends, track suppression
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS email_log (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            email_type  VARCHAR(50) NOT NULL,
            sent_at     TIMESTAMPTZ DEFAULT NOW(),
            resend_id   VARCHAR(255),
            status      VARCHAR(20) DEFAULT 'sent',
            UNIQUE (user_id, email_type)
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_email_log_user_id ON email_log(user_id);"
    )
    # enable pg_cron (confirmed available 1.6.4, not installed per Phase 1)
    # IF NOT EXISTS makes this idempotent; requires sufficient privileges on Supabase direct DB
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_cron;")
    # pg_net needed for HTTP calls from pg_cron jobs (optional)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_net;")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS email_log;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS onboarding_completed_at;")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS email_suppressed;")
    # do not drop pg_cron/pg_net extensions on downgrade — other jobs may depend on them
