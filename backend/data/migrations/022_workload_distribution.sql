-- PHASE 25: CHIP WORKLOAD DISTRIBUTION
-- Task Tracking Registry



CREATE TABLE IF NOT EXISTS cluster_tasks (
    task_id TEXT PRIMARY KEY,
    chip_slug TEXT NOT NULL,
    worker_node_id TEXT REFERENCES cluster_nodes(node_id),
    requesting_user_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    execution_context TEXT DEFAULT '{}',
    result_payload TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_TEXT ON cluster_tasks(status);
CREATE INDEX IF NOT EXISTS idx_task_worker ON cluster_tasks(worker_node_id);
