-- Fase 94: Tactical Telemetry & Forensics for Atomic Push
CREATE TABLE IF NOT EXISTS atomic_push_forensics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    push_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- PUSH_STARTED, STEP_STARTED, STEP_COMPLETED, STEP_BLOCKED, AUTHORITY_INJECTED, etc.
    step_index INTEGER,
    handoff_id TEXT,
    actor TEXT DEFAULT 'system',
    status_before TEXT,
    status_after TEXT,
    payload TEXT, -- JSON blob with details
    integrity_hash TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_forensics_push ON atomic_push_forensics(push_id);
