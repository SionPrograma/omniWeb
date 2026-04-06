-- Fase 95: Governed Rollback for Atomic Push
CREATE TABLE IF NOT EXISTS atomic_rollback_sessions (
    rollback_id TEXT PRIMARY KEY,
    push_id TEXT NOT NULL,
    state TEXT DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, BLOCKED, ABORTED, FAILED_SAFELY
    steps TEXT, -- JSON array of rollback steps
    current_step_index INTEGER DEFAULT 0,
    blocking_reason TEXT,
    authority_required TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rollback_push ON atomic_rollback_sessions(push_id);
