-- OMNIWEB — BLOQUE: GOVERNANCE MULTI-CONTEXT SYNC HARVESTER
-- Migración 120: Cosecha y promoción de sabiduría confirmada entre múltiples proyectos.

CREATE TABLE IF NOT EXISTS governance_wisdom_harvests (
    harvest_id TEXT PRIMARY KEY,
    atlas_node_id TEXT NOT NULL,
    proposed_level TEXT, -- LOCAL_PATTERN, STRONG_BASELINE, CROSS_CONTEXT_TACTIC, CANDIDATE_POLICY
    confirmation_count INTEGER DEFAULT 0,
    contradiction_count INTEGER DEFAULT 0,
    project_count INTEGER DEFAULT 0,
    context_diversity_score REAL DEFAULT 0.0,
    rationale TEXT,
    transfer_risk REAL,
    creator_decision TEXT DEFAULT 'PENDING', -- ACCEPTED, REJECTED, POSTPONED
    is_applied BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ADD project_id to syncs for diversity tracking (Phase 120 Additive)
-- Check if column exists first (or just PRAGMA if in many SQL flavors)
-- Assuming Sqlite 3.35+
-- ALTER TABLE governance_post_mission_syncs ADD COLUMN project_id TEXT;

CREATE INDEX IF NOT EXISTS idx_harvest_node ON governance_wisdom_harvests(atlas_node_id);
CREATE INDEX IF NOT EXISTS idx_harvest_decision ON governance_wisdom_harvests(creator_decision);
