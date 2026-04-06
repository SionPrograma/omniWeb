-- MIGRATION 108: GOVERNANCE FUSION ARCHITECTURE
-- OmniWeb: Tactically unifies Debt, Pressure, and Advisory into a single operational snapshot.

CREATE TABLE IF NOT EXISTS governance_fusion_snapshots (
    fusion_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL, -- MISSION, HANDOFF, DOMAIN
    fused_status TEXT NOT NULL, -- NOMINAL, WATCH, UNDER_DEBT, PRESSURED, STRUCTURALLY_COMPROMISED, IMMEDIATE_REVIEW
    severity_band TEXT NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
    rationale TEXT,
    next_action TEXT,
    
    -- Source Snapshot (Cached for traceability)
    debt_state TEXT,
    pressure_state TEXT,
    advisory_state TEXT,
    base_compromise_state TEXT,
    
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fusion_target ON governance_fusion_snapshots(target_id);
