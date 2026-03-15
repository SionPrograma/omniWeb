-- Migration 027: AI Host Memory Persistence Bridge
-- Goal: Provide stable UUID-based persistence for IdeaCapture and KnowledgeGraph.

CREATE TABLE IF NOT EXISTS ai_host_ideas (
    id TEXT PRIMARY KEY,
    timestamp REAL,
    author TEXT,
    content TEXT,
    tags TEXT, -- JSON
    related_nodes TEXT -- JSON
);

CREATE TABLE IF NOT EXISTS ai_host_knowledge_nodes (
    id TEXT PRIMARY KEY,
    title TEXT,
    description TEXT,
    tags TEXT, -- JSON
    metadata TEXT, -- JSON
    created_at REAL
);

CREATE TABLE IF NOT EXISTS ai_host_knowledge_edges (
    source_id TEXT,
    target_id TEXT,
    PRIMARY KEY (source_id, target_id),
    FOREIGN KEY (source_id) REFERENCES ai_host_knowledge_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES ai_host_knowledge_nodes(id) ON DELETE CASCADE
);
