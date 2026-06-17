-- Migration 006: Create workspace_members table
CREATE TABLE workspace_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(20) DEFAULT 'member',
    invited_at      TIMESTAMPTZ DEFAULT NOW(),
    accepted_at     TIMESTAMPTZ,
    
    UNIQUE(workspace_id, user_id)
);