-- Migration 005: Create templates table
CREATE TABLE templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    template_type   VARCHAR(50) DEFAULT 'marketing',
    config          JSONB NOT NULL DEFAULT '{}',
    is_default      BOOLEAN DEFAULT FALSE,
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_templates_user_id ON templates(user_id);

-- Trigger for templates table
CREATE TRIGGER templates_updated_at
  BEFORE UPDATE ON templates
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();