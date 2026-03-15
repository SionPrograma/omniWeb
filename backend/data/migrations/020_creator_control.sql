-- Migration 020: Creator Control Plane (Phase 23)
-- Infrastructure for high-level governance

CREATE TABLE IF NOT EXISTS system_governance (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    duration_minutes INTEGER NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'SCHEDULED', -- 'SCHEDULED', 'ACTIVE', 'COMPLETED', 'CANCELLED'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    creator_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS global_announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'INFO', -- 'INFO', 'WARNING', 'CRITICAL'
    creator_id TEXT NOT NULL,
    expires_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

-- Initialize system mode if not exists
INSERT OR IGNORE INTO system_governance (key, value, updated_by) VALUES ('system_mode', 'live', 'system');

CREATE INDEX IF NOT EXISTS idx_maintenance_status ON maintenance_schedules(status);
CREATE INDEX IF NOT EXISTS idx_announcements_active ON global_announcements(is_active, expires_at);
