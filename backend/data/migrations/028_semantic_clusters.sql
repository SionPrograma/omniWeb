-- Migration 028: AI Host Semantic Clusters
-- Goal: Stable persistence for semantic groupings of ideas and knowledge nodes.

CREATE TABLE IF NOT EXISTS ai_host_clusters (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT, -- JSON
    node_ids TEXT, -- JSON array of KnowledgeNode IDs
    created_at REAL,
    updated_at REAL
);

-- Index for title search
CREATE INDEX IF NOT EXISTS idx_ai_host_clusters_title ON ai_host_clusters(title);
