-- Migration 004: Create reports table
CREATE TABLE reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    
    -- Report Identity
    title           VARCHAR(255) NOT NULL,
    template_type   VARCHAR(50) DEFAULT 'marketing',
    status          VARCHAR(20) DEFAULT 'pending',
    
    -- Input Data
    source_type     VARCHAR(20) DEFAULT 'csv',
    source_url      TEXT,
    source_filename VARCHAR(255),
    row_count       INTEGER,
    column_count    INTEGER,
    
    -- Report Config
    config          JSONB DEFAULT '{}',
    
    -- Output
    pdf_url         TEXT,
    ppt_url         TEXT,
    share_token     VARCHAR(64),
    share_expires_at TIMESTAMPTZ,
    share_view_count INTEGER DEFAULT 0,
    
    -- AI Content
    ai_summary      TEXT,
    ai_insights     JSONB DEFAULT '[]',
    ai_anomalies    JSONB DEFAULT '[]',
    
    -- Performance
    generation_time_seconds FLOAT,
    error_message   TEXT,
    
    -- Metadata
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX idx_reports_share_token ON reports(share_token);
CREATE UNIQUE INDEX idx_reports_share_token_unique ON reports(share_token) WHERE share_token IS NOT NULL;

-- Trigger for reports table
CREATE TRIGGER reports_updated_at
  BEFORE UPDATE ON reports
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();