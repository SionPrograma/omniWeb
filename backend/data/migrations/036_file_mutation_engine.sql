-- Migration 036: File Mutation Engine Logs
-- Goal: Track all file changes performed by Builder/Copilot for audit and rollback.

CREATE TABLE IF NOT EXISTS builder_mutations (
    id TEXT PRIMARY KEY,
    batch_id TEXT,
    task_id TEXT,
    module_id TEXT,
    files_affected TEXT, -- JSON array of paths
    operations TEXT, -- JSON array of op types
    status TEXT NOT NULL, -- 'SUCCESS', 'FAILED', 'ROLLED_BACK'
    error_message TEXT,
    origin TEXT, -- 'Builder', 'Copilot'
    timestamp REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mutations_task ON builder_mutations(task_id);
CREATE INDEX IF NOT EXISTS idx_mutations_batch ON builder_mutations(batch_id);
