-- Migration 002: Create uploads table
CREATE TABLE uploads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- File info
    filename        VARCHAR(255) NOT NULL,
    file_url        TEXT NOT NULL,
    file_size_bytes INTEGER,
    source_type     VARCHAR(20) DEFAULT 'csv',

    -- Parsed metadata
    row_count       INTEGER,
    column_count    INTEGER,
    columns_meta    JSONB DEFAULT '[]',

    -- Lifecycle
    expires_at      TIMESTAMPTZ DEFAULT NOW() + interval '24 hours',
    used            BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_expires_at ON uploads(expires_at) WHERE used = FALSE;