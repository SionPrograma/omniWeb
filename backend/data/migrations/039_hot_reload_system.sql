-- Migration: Hot Reload System
-- Description: Logs for dynamic module reloads executed by the HotReloadEngine.

CREATE TABLE IF NOT EXISTS hot_reload_logs (
    id TEXT PRIMARY KEY,
    module_name TEXT NOT NULL,
    files_changed TEXT NOT NULL, -- JSON-encoded list of files that triggered this reload
    status TEXT NOT NULL,        -- 'SUCCESS' or 'FAILED'
    error_message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
