-- Migration 018: Asset & Workspace Sync Engine (Phase 21)

CREATE TABLE IF NOT EXISTS sync_devices (
    device_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_name TEXT,
    last_sync DATETIME,
    trust_level INTEGER DEFAULT 1,
    metadata TEXT, -- JSON platform info
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS sync_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT, -- 'UPLOAD', 'DOWNLOAD', 'CONFLICT_RESOLVED'
    target_sector TEXT, -- 'logbook', 'graph', 'assets', 'settings'
    status TEXT, -- 'SUCCESS', 'FAILED', 'WARNING'
    payload_summary TEXT, -- Brief summary of changed items
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (device_id) REFERENCES sync_devices(device_id)
);

-- For tracking deletions across devices (Tombstones)
CREATE TABLE IF NOT EXISTS sync_tombstones (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    target_type TEXT, -- 'logbook', 'graph'
    original_id TEXT,
    deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_devices_user ON sync_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_audit_user ON sync_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_tombstones_user ON sync_tombstones(user_id);
