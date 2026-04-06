-- OMNIWEB MIGRATION 054: MISSION MULTI-HANDOFF STORAGE
-- Enables holding multiple mission proposals before they enter the execution pipeline.

CREATE TABLE IF NOT EXISTS mission_handoffs (
    handoff_id TEXT PRIMARY KEY,
    briefing_title TEXT NOT NULL,
    objective TEXT NOT NULL,
    surface_affected TEXT, -- Store as JSON string array
    constraints TEXT, -- Store as JSON string array
    risk_level TEXT DEFAULT 'low',
    execution_style TEXT DEFAULT 'with_confirmation',
    readiness_state TEXT DEFAULT 'PENDING', -- PENDING, READY, BLOCKED, DRAFT, ABORTED, ARCHIVED
    source_type TEXT DEFAULT 'chat',
    gate_data TEXT, -- Store gate structure as JSON
    priority INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_handoff_state ON mission_handoffs(readiness_state);
CREATE INDEX IF NOT EXISTS idx_handoff_priority ON mission_handoffs(priority);
