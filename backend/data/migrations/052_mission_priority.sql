-- Phase 52: Mission Scheduling & Priority Engine
-- Adds metadata for intelligent workload prioritization

ALTER TABLE system_missions ADD COLUMN priority_score FLOAT DEFAULT 0.0;
ALTER TABLE system_missions ADD COLUMN priority_class TEXT DEFAULT 'NORMAL';
ALTER TABLE system_missions ADD COLUMN readiness_state TEXT DEFAULT 'READY';

-- Indexing for fast retrieval in sorting
CREATE INDEX IF NOT EXISTS idx_mission_priority ON system_missions(priority_score);
CREATE INDEX IF NOT EXISTS idx_mission_readiness ON system_missions(readiness_state);
