-- Migration 035: Builder Execution Engine
CREATE TABLE IF NOT EXISTS builder_tasks (
    id TEXT PRIMARY KEY,
    roadmap_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL, -- PENDING, EXECUTING, COMPLETED, FAILED, CANCELLED
    progress REAL DEFAULT 0,
    current_module_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT -- JSON with settings, results, etc.
);

CREATE TABLE IF NOT EXISTS builder_modules (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL, -- PENDING, READY, EXECUTING, COMPLETED, FAILED
    progress REAL DEFAULT 0,
    sequence_order INTEGER NOT NULL,
    module_type TEXT, -- e.g., 'initialization', 'implementation', 'audit'
    payload TEXT, -- JSON with step data
    result TEXT, -- JSON result
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES builder_tasks(id) ON DELETE CASCADE
);
