-- Migration 033: Database Hardening
-- Goal: Ensure foreign key integrity and unique constraints for project lineage.

-- 1. In SQLite, we can't easily ALTER TABLE to add UNIQUE or MODIFY FKs. 
-- We must recreate the tables with proper constraints if we want full enforcement.
-- However, for now, we can add a UNIQUE INDEX which partially satisfies SQLite requirements 
-- for FK targets in newer versions, but the safest way is a UNIQUE constraint.

-- Let's try to add the UNIQUE index first as it's non-destructive.
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_project_slug ON ai_host_project_lineage(project_slug);

-- 2. Ensure ai_host_project_activity is properly indexed and constrained.
-- (Already exists, but ensuring the index on project_slug is there)
CREATE INDEX IF NOT EXISTS idx_activity_project_slug ON ai_host_project_activity(project_slug);
