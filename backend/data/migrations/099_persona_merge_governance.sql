-- OMNIWEB MIGRATION 099: PERSONA MERGE GOVERNANCE
-- Stores role-based merge decisions and audit history.

ALTER TABLE roadmap_branches ADD COLUMN persona_verdict TEXT;

CREATE TABLE IF NOT EXISTS persona_merge_audits (
    audit_id TEXT PRIMARY KEY,
    branch_id TEXT NOT NULL,
    state TEXT NOT NULL, 
    severity TEXT,
    rationale TEXT,
    blocking_roles TEXT, 
    compensations TEXT, 
    bias_score REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_branch ON persona_merge_audits(branch_id);
