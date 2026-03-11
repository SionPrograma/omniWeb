-- Migration 003: AI Session Context
CREATE TABLE IF NOT EXISTS ai_session_context (
    session_id TEXT PRIMARY KEY,
    active_chips TEXT,  -- JSON list
    last_commands TEXT, -- JSON list
    user_preferences TEXT, -- JSON object
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_ai_session ON ai_session_context(session_id);
