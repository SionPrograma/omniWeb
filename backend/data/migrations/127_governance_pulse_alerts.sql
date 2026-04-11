-- OMNI_CATALYST_V0.7: Strategic Drift Alerting Store
CREATE TABLE IF NOT EXISTS governance_pulse_alerts (
    alert_id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL, -- POLICY_DRIFT, WISDOM_CONTRADICTOR, DOMAIN_BIAS, PROTOCOL_DRIFT
    subject_ref TEXT NOT NULL, -- pattern string, node_id, or domain_id
    occurrence_count INTEGER DEFAULT 1,
    confidence TEXT DEFAULT 'OBSERVATION', -- OBSERVATION, ELEVATED, CRITICAL
    rationale TEXT,
    evidence_ids TEXT, -- JSON list of ledger_id or sync_id
    domain_context TEXT,
    status TEXT DEFAULT 'PENDING_REVIEW', -- PENDING_REVIEW, APPLIED, DISMISSED, IGNORED
    project_id TEXT DEFAULT 'PROJECT_OMNIWEB_PROD',
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update engine parameters for drift sensitivity
INSERT OR IGNORE INTO governance_engine_parameters (param_id, engine_name, param_key, current_value, default_value, description)
VALUES ('P5', 'DRIFT_ADVISOR', 'PULSE_THRESHOLD', 3, 3, 'Minimum recurrences to trigger a pulse alert.');

INSERT OR IGNORE INTO governance_engine_parameters (param_id, engine_name, param_key, current_value, default_value, description)
VALUES ('P6', 'DRIFT_ADVISOR', 'PULSE_WINDOW_DAYS', 7, 7, 'Lookback window for signal consolidation.');
