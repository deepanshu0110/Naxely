-- Migration 008: Create scheduled_reports table
CREATE TABLE scheduled_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id     UUID REFERENCES templates(id) ON DELETE SET NULL,
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    
    name            VARCHAR(255) NOT NULL,
    frequency       VARCHAR(20) NOT NULL,
    next_run_at     TIMESTAMPTZ NOT NULL,
    last_run_at     TIMESTAMPTZ,
    
    -- Data source
    sheets_url      TEXT,
    
    -- Email recipients
    recipient_emails TEXT[] NOT NULL,
    
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scheduled_reports_next_run ON scheduled_reports(next_run_at) WHERE is_active = TRUE;