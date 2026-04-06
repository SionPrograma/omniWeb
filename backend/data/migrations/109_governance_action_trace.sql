-- OMNIWEB MIGRATION 109: GOVERNANCE ACTION TRACE SYSTEM
-- OmniWeb: Tactically links risk signals to decisions and their forensic outcomes.

CREATE TABLE IF NOT EXISTS governance_action_traces (
    trace_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL, -- MISSION, DOMAIN, HANDOFF
    source_snapshot_id TEXT, -- Link to governance_fusion_snapshots
    
    -- Decision Context
    creator_action TEXT NOT NULL, -- ACCEPT_RISK, REBASE, FREEZE, IGNORE, ESCALATE, CLOSE_DEBT
    initial_severity TEXT, -- Severity band at the time of action
    initial_fused_status TEXT, 
    
    -- Forensic Outcome
    outcome_status TEXT DEFAULT 'PENDING_OUTCOME', -- EFFECTIVE, PARTIAL_RELIEF, NO_EFFECT, DEGRADED_AFTER_ACTION, PENDING
    current_severity TEXT,
    severity_delta REAL DEFAULT 0.0, -- Negative = relief, Positive = escalation
    
    rationale_summary TEXT,
    confidence REAL DEFAULT 1.0,
    
    -- Metadata
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_recommended_action TEXT
);

CREATE INDEX IF NOT EXISTS idx_trace_target ON governance_action_traces(target_id);
CREATE INDEX IF NOT EXISTS idx_trace_snapshot ON governance_action_traces(source_snapshot_id);
