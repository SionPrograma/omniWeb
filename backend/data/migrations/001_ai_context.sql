-- Migration 001: AI Host Context Memory System
CREATE TABLE IF NOT EXISTS ai_context_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Seed some initial context or settings if needed
INSERT INTO ai_context_memory (user_id, key, value) VALUES ('1', 'ai_personality', 'helpful_architect');
INSERT INTO ai_context_memory (user_id, key, value) VALUES ('1', 'preferred_language', 'es');
