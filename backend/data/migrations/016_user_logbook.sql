-- Migration 016: User Personal Logbook (Phase 17)
-- Scoped logbook for individual users with workspace parity

CREATE TABLE IF NOT EXISTS user_logbooks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_user_logbook_user ON user_logbooks(user_id);
CREATE INDEX IF NOT EXISTS idx_user_logbook_type ON user_logbooks(entry_type);
CREATE INDEX IF NOT EXISTS idx_user_logbook_time ON user_logbooks(timestamp);
