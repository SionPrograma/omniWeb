-- OMNIWEB MIGRATION 129: MODE-AWARE AUDIT LOGGING (V1.4)
-- This migration transforms admin_operations into a robust, mode-aware audit history.

-- 1. Snapshot/Backup current table if necessary (internal SQLite, not usually needed)

-- 2. Enhance admin_operations
ALTER TABLE admin_operations ADD COLUMN user_mode TEXT DEFAULT 'PUBLIC';
ALTER TABLE admin_operations ADD COLUMN permission_level TEXT DEFAULT 'NONE';
ALTER TABLE admin_operations ADD COLUMN outcome TEXT DEFAULT 'SUCCESS';
ALTER TABLE admin_operations ADD COLUMN resource_id TEXT;

-- 3. Enhance security_audit_logs for parity if used
ALTER TABLE security_audit_logs ADD COLUMN user_mode TEXT DEFAULT 'PUBLIC';
ALTER TABLE security_audit_logs ADD COLUMN permission_level TEXT DEFAULT 'NONE';
ALTER TABLE security_audit_logs ADD COLUMN outcome TEXT DEFAULT 'SUCCESS';

-- 4. New Indices for Audit Performance
CREATE INDEX IF NOT EXISTS idx_admin_ops_mode ON admin_operations(user_mode);
CREATE INDEX IF NOT EXISTS idx_admin_ops_resource ON admin_operations(resource_id);

-- MISSION ACCOMPLISHED: Schema is now mode-aware.
