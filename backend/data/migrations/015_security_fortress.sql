-- Migration 015: Creator Security Fortress (Phase 16)
-- Tables for trusted devices and security audit logs

CREATE TABLE IF NOT EXISTS trusted_devices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    device_name TEXT,
    signature_key TEXT NOT NULL,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS security_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    creator_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target_resource TEXT,
    payload_snapshot TEXT,
    hash_signature TEXT,
    device_id TEXT,
    FOREIGN KEY (creator_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_creator ON security_audit_logs(creator_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON security_audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_trusted_user_device ON trusted_devices(user_id, device_id);
