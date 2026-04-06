-- OMNIWEB — BLOQUE: GOVERNANCE POST-MISSION WISDOM SYNC
-- Migración 119: Sincronización explicable pos-misión entre ejecución real y Atlas de Sabiduría.

CREATE TABLE IF NOT EXISTS governance_post_mission_syncs (
    sync_id TEXT PRIMARY KEY,
    source_package_id TEXT NOT NULL,
    source_mission_id TEXT,
    source_atlas_node_ids TEXT, -- JSON list of node IDs referenced
    actual_outcome_type TEXT, -- WISDOM_CONFIRMED, WISDOM_PARTIAL, WISDOM_CONTRADICTED, EXECUTION_BIASED, INSUFFICIENT_SIGNAL
    preconditions_respected BOOLEAN,
    execution_context_quality REAL,
    proposed_confidence_delta REAL,
    proposed_reusability_delta REAL,
    rationale TEXT,
    supporting_evidence TEXT, -- JSON blob (autopsy link, roadside logs)
    creator_decision TEXT DEFAULT 'PENDING', -- ACCEPTED, REJECTED, POSTPONED
    is_applied BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_package ON governance_post_mission_syncs(source_package_id);
CREATE INDEX IF NOT EXISTS idx_sync_status ON governance_post_mission_syncs(creator_decision);
