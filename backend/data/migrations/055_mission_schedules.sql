-- OMNIWEB MIGRATION 055: MISSION MULTI-MISSION SCHEDULER
-- Enables planning and ordering sequences of mission proposals.

CREATE TABLE IF NOT EXISTS mission_schedules (
    schedule_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    ordered_handoff_ids TEXT NOT NULL, -- JSON list of strings (handoff_ids)
    dependency_hints TEXT, -- JSON map
    risk_chain TEXT, -- JSON map
    conflict_chain TEXT, -- JSON map
    rebase_required_flags TEXT, -- JSON list
    recommended_sequence TEXT, -- JSON list
    readiness_state TEXT DEFAULT 'DRAFT', -- DRAFT, READY, EXECUTING, ARCHIVED
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schedule_state ON mission_schedules(readiness_state);
