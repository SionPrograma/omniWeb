-- Phase 40: Mission State Persistence
-- Establishes the anchor for long-term operational continuity

CREATE TABLE IF NOT EXISTS system_missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT UNIQUE NOT NULL,
    active_goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN', -- OPEN, PAUSED, BLOCKED, COMPLETED, FAILED
    plan_id TEXT,
    completed_steps TEXT, -- JSON array of strings/objects
    pending_steps TEXT, -- JSON array of strings/objects
    blocked_reasons TEXT, -- JSON array
    related_targets TEXT, -- JSON array of file paths or chip names
    context_snap TEXT, -- JSON blob of last known relevant state
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mission_status ON system_missions(status);
CREATE INDEX IF NOT EXISTS idx_mission_id ON system_missions(mission_id);
