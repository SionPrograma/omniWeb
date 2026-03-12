-- Phase R: Semantic Layer Implementation
-- VERSION: v0.6.9

CREATE TABLE IF NOT EXISTS semantic_embeddings (
    node_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    embedding TEXT NOT NULL,
    text_content TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster filtering by source type (Knowledge Node vs Memory)
CREATE INDEX IF NOT EXISTS idx_semantic_source ON semantic_embeddings(source_type);
