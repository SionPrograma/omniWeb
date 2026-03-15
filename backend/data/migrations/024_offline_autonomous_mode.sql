-- PHASE 27: OFFLINE AUTONOMOUS MODE
-- Operation Sync Backlog

CREATE TABLE IF NOT EXISTS cluster_sync_backlog (
    sync_id TEXT PRIMARY KEY,
    operation_type TEXT NOT NULL, -- logbook, task, knowledge, config
    payload TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending', -- pending, syncing, completed, failed
    retry_count INTEGER DEFAULT 0,
    conflict_resolution_strategy TEXT DEFAULT 'LWW' -- Last Write Wins
);

CREATE INDEX IF NOT EXISTS idx_sync_status ON cluster_sync_backlog(status);
CREATE INDEX IF NOT EXISTS idx_sync_time ON cluster_sync_backlog(timestamp);

-- Update cluster_nodes to track local/mesh mode
ALTER TABLE cluster_nodes ADD COLUMN operation_mode TEXT DEFAULT 'mesh'; -- mesh, offline
