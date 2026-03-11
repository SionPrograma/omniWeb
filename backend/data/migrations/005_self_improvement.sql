-- Migration 005: Self Improvement Proposals
CREATE TABLE IF NOT EXISTS improvement_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_type TEXT NOT NULL,
    description TEXT NOT NULL,
    recommended_action TEXT,
    status TEXT DEFAULT 'pending', -- pending, accepted, rejected, ignored
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for searching proposals
CREATE INDEX IF NOT EXISTS idx_proposal_status ON improvement_proposals(status);
