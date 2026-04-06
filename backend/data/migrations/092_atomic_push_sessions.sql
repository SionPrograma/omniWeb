-- Final de la Fase 92: Atomic Push Execution Persistence
CREATE TABLE IF NOT EXISTS atomic_push_sessions (
    push_id TEXT PRIMARY KEY,
    roadmap_group_id TEXT NOT NULL,
    state TEXT DEFAULT 'READY', 
    current_step_index INTEGER DEFAULT 0,
    execution_plan TEXT NOT NULL, -- JSON List of Step objects
    step_statuses TEXT, -- JSON Dict mapping index to step-specific status
    blocking_reason TEXT,
    authority_required TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
