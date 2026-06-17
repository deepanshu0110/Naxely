-- Migration 012: Add partial unique index for upload_id dedup
-- Prevents double-submission race: two concurrent requests for the same
-- upload_id cannot both create a pending/processing report.
-- Mirrors the payment_events idempotency pattern (migration 007).
CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_active_upload
ON reports (user_id, (config->>'upload_id'))
WHERE status IN ('pending', 'processing') AND deleted_at IS NULL;
