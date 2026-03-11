-- Migration 004: Usage Tracking Table
CREATE TABLE IF NOT EXISTS usage_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    chip_slug TEXT,
    user_session TEXT,
    metadata TEXT, -- JSON object
    timestamp TEXT DEFAULT (datetime('now'))
);

-- Index for analytics performance
CREATE INDEX IF NOT EXISTS idx_usage_type ON usage_events(event_type);
CREATE INDEX IF NOT EXISTS idx_usage_chip ON usage_events(chip_slug);
CREATE INDEX IF NOT EXISTS idx_usage_time ON usage_events(timestamp);
