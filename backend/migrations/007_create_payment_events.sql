-- Migration 007: Create payment_events table
CREATE TABLE payment_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    
    event_type      VARCHAR(100) NOT NULL,
    dodo_event_id   VARCHAR(255) UNIQUE,
    payload         JSONB NOT NULL,
    processed       BOOLEAN DEFAULT FALSE,
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payment_events_user_id ON payment_events(user_id);
CREATE INDEX idx_payment_events_type ON payment_events(event_type);
CREATE UNIQUE INDEX idx_payment_events_dodo_id ON payment_events(dodo_event_id);