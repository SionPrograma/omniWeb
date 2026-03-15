-- Migration 032: AI Host Evolution Reports
-- Goal: Persist technical evolution reports that summarize project progress.

CREATE TABLE IF NOT EXISTS ai_host_evolution_reports (
    id TEXT PRIMARY KEY,
    project_slug TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    source_cluster_id TEXT,
    source_node_ids TEXT, -- JSON array
    lineage_ids TEXT, -- JSON array
    activity_event_ids TEXT, -- JSON array
    suggested_next_steps TEXT, -- JSON array
    created_at REAL,
    FOREIGN KEY (project_slug) REFERENCES ai_host_project_lineage(project_slug) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reports_project_slug ON ai_host_evolution_reports(project_slug);
