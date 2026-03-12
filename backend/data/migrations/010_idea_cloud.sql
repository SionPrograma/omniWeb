-- Migration 010: Idea Cloud Engine Data Structures
CREATE TABLE IF NOT EXISTS idea_cloud (
    id TEXT PRIMARY KEY,
    raw_thought TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_context TEXT, -- JSON
    topics TEXT, -- JSON array
    sentiment REAL,
    linked_nodes TEXT, -- JSON array
    linked_memories TEXT, -- JSON array
    is_processed INTEGER DEFAULT 0,
    suggested_actions TEXT -- JSON
);

CREATE TABLE IF NOT EXISTS idea_clusters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    idea_ids TEXT, -- JSON array
    summary TEXT,
    emerging_project INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
