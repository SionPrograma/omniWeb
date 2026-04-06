-- OMNIWEB MIGRATION 102: CREATOR CORE ARBITRATION
-- Infrastructure for handling escalated branch conflicts.

CREATE TABLE IF NOT EXISTS branch_arbitrations (
    arbitration_id TEXT PRIMARY KEY,
    branch_id TEXT NOT NULL,
    escalation_reason TEXT,
    decision TEXT NOT NULL, -- APPROVE_ANYWAY, APPROVE_WITH_CONDITIONS, REQUIRE_FURTHER_COMPENSATION, POSTPONE, REJECT_VETO
    rationale TEXT,
    conditions TEXT, -- JSON list of conditions if any
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(branch_id) REFERENCES roadmap_branches(branch_id)
);

-- Update branches to track if they are under arbitration or have had an arbitration override.
ALTER TABLE roadmap_branches ADD COLUMN arbitration_id TEXT;
ALTER TABLE roadmap_branches ADD COLUMN is_arbitrated BOOLEAN DEFAULT 0;
