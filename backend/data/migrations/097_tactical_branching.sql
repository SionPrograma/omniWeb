-- OMNIWEB MIGRATION 097: TACTICAL BRANCHING SCHEMA
-- Enables creation, management, and comparison of roadmap branches.

CREATE TABLE IF NOT EXISTS roadmap_branches (
    branch_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    origin_branch_id TEXT DEFAULT 'main',
    branch_type TEXT DEFAULT 'tactical', -- tactical, experiment, domain, sequence
    base_snapshot_id TEXT,
    branch_state TEXT DEFAULT 'ACTIVE', -- ACTIVE, SIMULATED, MERGED, DISCARDED
    branch_owner_persona TEXT DEFAULT 'CREATOR_CORE',
    
    -- Strategic Metadata
    divergence_score REAL DEFAULT 0.0,
    simulation_summary TEXT, -- JSON Summary
    merge_readiness REAL DEFAULT 0.0,
    constitutional_status TEXT DEFAULT 'PENDING', -- PENDING, PASSED, VIOLATED
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Add branch_id to existing tables if not present
-- Note: SQLite doesn't support IF NOT EXISTS in ALTER TABLE easily, 
-- but we can use a script or just assume clean state for this phase.

ALTER TABLE mission_handoffs ADD COLUMN branch_id TEXT DEFAULT 'main';
ALTER TABLE mission_schedules ADD COLUMN branch_id TEXT DEFAULT 'main';

CREATE INDEX IF NOT EXISTS idx_branch_id_handoffs ON mission_handoffs(branch_id);
CREATE INDEX IF NOT EXISTS idx_branch_id_schedules ON mission_schedules(branch_id);
