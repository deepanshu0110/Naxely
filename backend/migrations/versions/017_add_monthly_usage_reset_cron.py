"""Wire up monthly usage reset via pg_cron (daily 00:01 UTC)

P0 fix for reset_monthly_usage having no caller — free users stuck at 3/3.

Revision ID: 017
Revises: 016
Create Date: 2026-08-26

Decision: pg_cron, not cron-job.org / Render cron.
Reason: reset logic is a single pure-SQL UPDATE (no Python needed), so pg_cron
avoids adding a new authenticated HTTP endpoint surface and an external cron
dependency that requires manual dashboard registration outside this session.
Daily cadence matches the existing lifecycle-email pattern and is cheap:
WHERE usage_reset_at <= NOW() only touches rows whose reset date has passed
(~0-1 rows per free user per month). The same pg_cron + pg_net extensions
were already created IF NOT EXISTS in 015, so this migration only schedules.

Verification (requires Supabase SQL Editor, cannot be fully exercised in
sandbox without a live DB with pg_cron superuser):
  SELECT * FROM pg_extension WHERE extname = 'pg_cron';
  SELECT jobid, jobname, schedule, command, database, active
    FROM cron.job WHERE jobname = 'monthly-usage-reset-daily';
Should return 1 row: schedule '1 0 * * *', command = UPDATE ..., active = true
  SELECT * FROM cron.job_run_details WHERE jobid = <id> ORDER BY start_time DESC LIMIT 5;
For manual instant test (no waiting for midnight):
  UPDATE users SET reports_this_month = 0,
    usage_reset_at = date_trunc('month', NOW() + interval '1 month')
    WHERE usage_reset_at <= NOW();

Backfill: the same UPDATE is executed immediately in this migration so
currently-stuck free users (reports_this_month >=3, usage_reset_at <= NOW())
are unstuck without waiting for the first cron tick at 00:01 UTC.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions — idempotent (already in 015, but re-assert for fresh DBs that skipped 015)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_cron;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_net;")

    # Immediate backfill: unstuck any free users whose reset date is already past.
    # This is the same predicate as reset_monthly_usage() — safe to run even on a fresh DB (0 rows).
    # WHERE reports_this_month != 0 is an optimization to avoid touching untouched rows, but not
    # strictly required; we keep the exact production predicate for parity.
    op.execute(
        """
        UPDATE users
        SET reports_this_month = 0,
            usage_reset_at = date_trunc('month', NOW() + interval '1 month')
        WHERE usage_reset_at <= NOW();
        """
    )

    # Schedule daily 00:01 UTC job — idempotent. pg_cron's cron.unschedule throws if job
    # doesn't exist on some builds, so wrap in a DO block that swallows the exception.
    op.execute(
        """
        DO $$
        BEGIN
            PERFORM cron.unschedule('monthly-usage-reset-daily');
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END
        $$;
        """
    )

    # Note: command string uses $$ dollar quoting; pg_cron runs it directly in the DB (pure SQL,
    # no Python call needed — matches reset_monthly_usage() exactly).
    op.execute(
        """
        SELECT cron.schedule(
            'monthly-usage-reset-daily',
            '1 0 * * *',
            $$UPDATE users SET reports_this_month = 0, usage_reset_at = date_trunc('month', NOW() + interval '1 month') WHERE usage_reset_at <= NOW()$$
        );
        """
    )


def downgrade() -> None:
    # Remove schedule, keep extensions (other jobs may depend), do not revert backfill.
    op.execute(
        """
        DO $$
        BEGIN
            PERFORM cron.unschedule('monthly-usage-reset-daily');
        EXCEPTION WHEN OTHERS THEN
            NULL;
        END
        $$;
        """
    )
