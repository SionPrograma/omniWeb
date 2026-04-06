-- OMNIWEB MIGRATION 100: COMPENSATION EFFECTIVENESS AUDIT
-- Tracks the impact of tactical compensations on branch health.

CREATE TABLE IF NOT EXISTS compensation_effectiveness_audits (
    audit_id TEXT PRIMARY KEY,
    branch_id TEXT NOT NULL,
    compensation_id TEXT NOT NULL,
    effectiveness_state TEXT NOT NULL, -- EFFECTIVE, PARTIAL, INSUFFICIENT, REDUNDANT, BACKFIRED
    before_state TEXT,
    after_state TEXT,
    friction_delta REAL,
    readiness_delta REAL,
    recommended_next_action TEXT,
    rationale TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_comp_effect_branch ON compensation_effectiveness_audits(branch_id);
CREATE INDEX IF NOT EXISTS idx_comp_effect_comp ON compensation_effectiveness_audits(compensation_id);
