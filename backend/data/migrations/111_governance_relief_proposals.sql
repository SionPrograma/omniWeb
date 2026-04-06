-- OMNIWEB MIGRATION 111: GOVERNANCE RECOVERY MISSION PROPOSALS
-- Infrastructure for pre-designing relief missions based on structural friction hotspots.

CREATE TABLE IF NOT EXISTS governance_relief_proposals (
    proposal_id TEXT PRIMARY KEY,
    source_heatmap_node TEXT, -- Affected domain
    relief_type TEXT, -- DOMAIN_RELIEF_MISSION, STRUCTURAL_HARDENING_MISSION, etc
    confidence REAL,
    rationale TEXT,
    proposed_objective TEXT,
    affected_domains TEXT, -- JSON or comma-separated list of technical surfaces
    expected_heat_reduction REAL,
    status TEXT DEFAULT 'PENDING', -- PENDING, ACCEPTED, REJECTED, POSTPONED
    associated_handoff_id TEXT, -- Link to the real mission once accepted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick lookup of active proposals per domain
CREATE INDEX IF NOT EXISTS idx_relief_proposals_domain ON governance_relief_proposals (source_heatmap_node, status);
