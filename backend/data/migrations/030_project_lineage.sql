-- Migration 030: AI Host Project Lineage / Semantic Bridge
-- Goal: Track the evolution of projects from ideas to physical chips.

CREATE TABLE IF NOT EXISTS ai_host_project_lineage (
    id TEXT PRIMARY KEY,
    project_slug TEXT NOT NULL,
    source_cluster_id TEXT,
    source_node_ids TEXT, -- JSON array of KnowledgeNode IDs
    source_draft_id TEXT,
    created_at REAL,
    updated_at REAL,
    related_events TEXT, -- JSON array of events/logs
    FOREIGN KEY (source_cluster_id) REFERENCES ai_host_clusters(id) ON DELETE SET NULL,
    FOREIGN KEY (source_draft_id) REFERENCES ai_host_project_drafts(id) ON DELETE SET NULL
);

-- Index for fast lookup by slug
CREATE INDEX IF NOT EXISTS idx_lineage_project_slug ON ai_host_project_lineage(project_slug);
