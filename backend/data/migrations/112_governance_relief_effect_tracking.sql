-- OMNIWEB MIGRATION 112: GOVERNANCE RELIEF EFFECT TRACKING
-- Adds structural resistance tracking to relief proposals.

ALTER TABLE governance_relief_proposals ADD COLUMN baseline_friction_score REAL DEFAULT 0.0;
ALTER TABLE governance_relief_proposals ADD COLUMN current_friction_score REAL DEFAULT 0.0;
ALTER TABLE governance_relief_proposals ADD COLUMN relief_outcome TEXT DEFAULT 'PENDING'; -- EFFECTIVE, PARTIAL, INEFFECTIVE, RESISTANT, PENDING
ALTER TABLE governance_relief_proposals ADD COLUMN observers_count INTEGER DEFAULT 0; -- Number of evaluations performed
ALTER TABLE governance_relief_proposals ADD COLUMN last_evaluation_at TIMESTAMP;

-- Registry for historical resistance snapshots
CREATE TABLE IF NOT EXISTS governance_structural_resistance_log (
    log_id TEXT PRIMARY KEY,
    domain TEXT,
    relief_mission_id TEXT,
    friction_at_start REAL,
    friction_at_eval REAL,
    delta REAL,
    eval_outcome TEXT,
    rationale TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
