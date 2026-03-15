-- Migration 031: Project Active Monitoring / Activity Events
-- Goal: Track file-level modifications and technical evolution within initialized projects.

CREATE TABLE IF NOT EXISTS ai_host_project_activity (
    id TEXT PRIMARY KEY,
    project_slug TEXT NOT NULL,
    event_type TEXT NOT NULL, -- e.g., 'MODIFIED', 'CREATED', 'DELETED'
    file_path TEXT,
    summary TEXT,
    created_at REAL,
    related_lineage_id TEXT,
    FOREIGN KEY (project_slug) REFERENCES ai_host_project_lineage(project_slug) ON DELETE CASCADE,
    FOREIGN KEY (related_lineage_id) REFERENCES ai_host_project_lineage(id) ON DELETE CASCADE
);

-- Index for cluster-based activity lookups
CREATE INDEX IF NOT EXISTS idx_activity_project_slug ON ai_host_project_activity(project_slug);
