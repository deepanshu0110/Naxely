-- Migration 010: Create additional indexes
-- Add indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_users_dodo_customer ON users(dodo_customer_id);