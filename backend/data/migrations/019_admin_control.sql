-- Migration 019: Admin Control Layer (Phase 22)

CREATE TABLE IF NOT EXISTS admin_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id TEXT NOT NULL,
    operation_type TEXT NOT NULL, -- 'DEPLOY', 'CONFIG', 'AUTH_CHANGE', 'REJECT_AI'
    target_resource TEXT,
    details TEXT, -- JSON details
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_suggestions (
    id TEXT PRIMARY KEY,
    suggestion_type TEXT NOT NULL, -- 'FIX', 'OPTIMIZE', 'NEW_CHIP'
    content TEXT NOT NULL, -- JSON content
    severity TEXT,
    status TEXT DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'REJECTED', 'MODIFIED'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME,
    reviewer_id TEXT,
    review_notes TEXT
);

CREATE TABLE IF NOT EXISTS system_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id TEXT NOT NULL,
    label TEXT NOT NULL,
    db_backup_path TEXT NOT NULL,
    fs_snapshot_path TEXT, -- Optional, for complex rollbacks
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_ops_timestamp ON admin_operations(timestamp);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_status ON ai_suggestions(status);
