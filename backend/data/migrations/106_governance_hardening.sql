-- OMNIWEB MIGRATION 106: GOVERNANCE HARDENING
-- Adds risk overrides and pressure timeline tracking for structural health.

CREATE TABLE IF NOT EXISTS governance_risk_overrides (
    override_id TEXT PRIMARY KEY,
    recommendation_id TEXT,
    target_id TEXT NOT NULL,
    override_type TEXT NOT NULL, -- STRATEGIC, TECHNICAL, URGENT
    risk_level TEXT,
    rationale TEXT,
    conditions TEXT, -- JSON or comma-separated
    is_active BOOLEAN DEFAULT 1,
    debt_state TEXT DEFAULT 'ACTIVE', -- ACTIVE, OVERDUE, DEGRADED, CLOSED
    review_at TIMESTAMP,
    last_reviewed_at TIMESTAMP,
    degradation_score REAL DEFAULT 0.0,
    next_required_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS governance_pressure_events (
    event_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- DEBT_DEGRADED, PRESSURE_OVERRIDDEN, CRITICAL_DEBT_VENCIDA
    source_advisory_id TEXT,
    risk_level TEXT,
    creator_decision TEXT,
    rationale TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
