-- Migration 006: User Behavior Patterns
CREATE TABLE IF NOT EXISTS user_behavior_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL, -- habit, routine, preference
    pattern_data TEXT NOT NULL, -- JSON object
    confidence REAL DEFAULT 0.0,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for pattern matching
CREATE INDEX IF NOT EXISTS idx_behavior_type ON user_behavior_patterns(pattern_type);
