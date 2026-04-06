-- OMNIWEB — BLOQUE: PRE-MISSION GOVERNANCE CHECK PERSISTENCE
-- Tracks the automated pre-checks performed before starting a mission or proposal.

CREATE TABLE IF NOT EXISTS pre_mission_governance_checks (
    check_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL, -- PROPOSAL, MISSION, PUSH
    branch_id TEXT DEFAULT 'main',
    resulting_status TEXT NOT NULL, -- SAFE_TO_START, START_WITH_WARNING, REVIEW_REQUIRED, REBASE_RECOMMENDED, FREEZE_UNTIL_RECOVERY, ESCALATE_TO_CREATOR_CORE
    rationale TEXT,
    signals_json TEXT, -- Serialized list of PreMissionCheckSignal objects
    creator_decision TEXT, -- CONTINUE, REVIEW, REBASE, FREEZE, ESCALATE
    confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup of the latest check for a target
CREATE INDEX IF NOT EXISTS idx_precheck_target ON pre_mission_governance_checks(target_id, created_at DESC);
