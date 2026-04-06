-- OMNIWEB MIGRATION 104: GOVERNANCE REBASE ADVISOR
-- Connects structural advisories with active missions to suggest rebase/freeze actions.

CREATE TABLE IF NOT EXISTS governance_advisories (
    advisory_id TEXT PRIMARY KEY,
    source_pattern_id TEXT,
    advisory_state TEXT DEFAULT 'PENDING', -- PENDING, ACCEPTED, DISMISSED, POSTPONED, IMPACT_CONFIRMED
    handoff_id TEXT, -- Linked mission if accepted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS governance_rebase_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    source_advisory_id TEXT,
    affected_handoff_id TEXT,
    affected_domain TEXT,
    recommendation_state TEXT DEFAULT 'PENDING', -- PENDING, REVIEWED, ACCEPTED, IGNORED, POSTPONED
    risk_level TEXT,
    suggested_action TEXT,
    rationale TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
