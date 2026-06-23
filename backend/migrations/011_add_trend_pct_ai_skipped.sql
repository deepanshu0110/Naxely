-- Migration 005: Add trend_pct and ai_skipped columns to reports
ALTER TABLE reports ADD COLUMN IF NOT EXISTS trend_pct FLOAT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS ai_skipped BOOLEAN DEFAULT FALSE;
