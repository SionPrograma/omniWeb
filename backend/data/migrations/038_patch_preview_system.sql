-- Migration 038: Patch Preview System
-- Goal: Store proposed file changes (diffs) for Creator approval.

CREATE TABLE IF NOT EXISTS builder_patch_previews (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    batch_data TEXT NOT NULL, -- JSON of the MutationBatch
    diff_data TEXT NOT NULL, -- JSON with diff information per file
    status TEXT NOT NULL, -- 'PENDING', 'APPROVED', 'REJECTED'
    decision_by TEXT, -- Role of the decider
    timestamp REAL NOT NULL,
    FOREIGN KEY (task_id) REFERENCES builder_tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_patch_task ON builder_patch_previews(task_id);
