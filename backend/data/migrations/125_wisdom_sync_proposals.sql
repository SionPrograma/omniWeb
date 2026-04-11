-- OMNIWEB — BLOQUE: GOVERNANCE POST-MISSION WISDOM SYNC
-- Migración 125: Tabla de Propuestas de Sincronización de Sabiduría

CREATE TABLE IF NOT EXISTS governance_wisdom_sync_proposals (
    proposal_id TEXT PRIMARY KEY,
    source_wisdom_node_id TEXT NOT NULL,
    source_mission_id TEXT NOT NULL,
    catalyst_trace_id TEXT,
    outcome_classification TEXT NOT NULL, -- WISDOM_CONFIRMED, WISDOM_PARTIAL, WISDOM_CONTRADICTED, WISDOM_INSUFFICIENT
    evidence_summary TEXT, -- Resumen técnico del match/mismatch
    confidence_delta REAL DEFAULT 0.0,
    status TEXT DEFAULT 'PENDING_REVIEW', -- PENDING_REVIEW, APPROVED, REJECTED, DEFERRED
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_wisdom_node_id) REFERENCES governance_wisdom_atlas_nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_wisdom_sync_pending ON governance_wisdom_sync_proposals(status);
