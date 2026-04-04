-- Migration 043: Multimodal Context History Persistence
-- Goal: Add traceability for visual evolution in missions.

-- Adding missing columns from Phase 21 baseline and the new history column
ALTER TABLE system_missions ADD COLUMN visual_context TEXT;
ALTER TABLE system_missions ADD COLUMN multimodal_history TEXT;

-- Index for history lookup if needed (though mostly accessed via mission_id)
CREATE INDEX IF NOT EXISTS idx_mission_history ON system_missions(mission_id);
