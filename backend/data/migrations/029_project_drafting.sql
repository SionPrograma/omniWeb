-- Migration 029: AI Host Project Drafting / Synthesis
-- Goal: Persist generated project drafts and cluster summaries.

CREATE TABLE IF NOT EXISTS ai_host_project_drafts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT,
    source_cluster_id TEXT,
    source_node_ids TEXT, -- JSON array
    suggested_modules TEXT, -- JSON array
    suggested_next_steps TEXT, -- JSON array
    created_at REAL,
    FOREIGN KEY (source_cluster_id) REFERENCES ai_host_clusters(id) ON DELETE SET NULL
);
