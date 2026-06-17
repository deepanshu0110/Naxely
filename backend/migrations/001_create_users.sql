-- Migration 001: Create users table
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    full_name       VARCHAR(255),
    avatar_url      TEXT,
    auth_provider   VARCHAR(50) DEFAULT 'email',
    
    -- Subscription
    tier            VARCHAR(20) DEFAULT 'free',
    tier_expires_at TIMESTAMPTZ,
    dodo_customer_id VARCHAR(255),
    dodo_subscription_id VARCHAR(255),
    
    -- AI Settings (encrypted)
    ai_provider     VARCHAR(20),
    encrypted_api_key TEXT,
    api_key_iv      TEXT,
    
    -- Branding (Pro+)
    logo_url        TEXT,
    brand_color     VARCHAR(7) DEFAULT '#6366F1',
    company_name    VARCHAR(255),
    
    -- Usage Tracking
    reports_this_month INTEGER DEFAULT 0,
    usage_reset_at  TIMESTAMPTZ DEFAULT date_trunc('month', NOW() + interval '1 month'),
    
    -- Metadata
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

-- Function to auto-update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();