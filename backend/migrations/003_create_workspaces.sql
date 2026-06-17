-- Migration 003: Create workspaces table
CREATE TABLE workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    name            VARCHAR(255) NOT NULL,
    client_name     VARCHAR(255),
    logo_url        TEXT,
    brand_color     VARCHAR(7),
    
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_workspaces_owner_id ON workspaces(owner_id);

-- Trigger for workspaces table
CREATE TRIGGER workspaces_updated_at
  BEFORE UPDATE ON workspaces
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();