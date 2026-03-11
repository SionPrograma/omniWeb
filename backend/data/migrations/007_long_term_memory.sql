-- Migration 007: Long Term Memory Engine
CREATE TABLE IF NOT EXISTS long_term_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT NOT NULL,
    source_chip TEXT,
    source_session TEXT,
    importance_score REAL DEFAULT 0.5,
    confidence_score REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memory_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    related_type TEXT NOT NULL,
    related_id TEXT NOT NULL,
    relationship TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (memory_id) REFERENCES long_term_memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memories_type ON long_term_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON long_term_memories(importance_score);
CREATE INDEX IF NOT EXISTS idx_memory_links_memory ON memory_links(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_links_related ON memory_links(related_type, related_id);
