-- Migration 034: Index Tuning for AI Host
-- Goal: Improve performance of memory search and timeline rendering.

CREATE INDEX IF NOT EXISTS idx_ideas_timestamp ON ai_host_ideas(timestamp);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_created ON ai_host_knowledge_nodes(created_at);
CREATE INDEX IF NOT EXISTS idx_clusters_title ON ai_host_clusters(title);
CREATE INDEX IF NOT EXISTS idx_project_activity_created ON ai_host_project_activity(created_at);
CREATE INDEX IF NOT EXISTS idx_evolution_reports_project ON ai_host_evolution_reports(project_slug);
