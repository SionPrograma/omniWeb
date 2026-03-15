-- Migration 014: Universal Identity Layer (Phase 15)
-- Extends the users table to support Multi-Provider OAuth

ALTER TABLE users ADD COLUMN provider TEXT DEFAULT 'local';
ALTER TABLE users ADD COLUMN provider_id TEXT;
ALTER TABLE users ADD COLUMN email TEXT;
ALTER TABLE users ADD COLUMN display_name TEXT;
ALTER TABLE users ADD COLUMN avatar TEXT;

-- Index for fast OAuth lookups
CREATE INDEX IF NOT EXISTS idx_user_provider ON users(provider, provider_id);
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);

-- Add last_login to users
ALTER TABLE users ADD COLUMN last_login DATETIME;
