-- Migration 049: Enhance system_locks for better lifecycle management
-- Adds status and released_at to support parallel mission governance

-- If the columns don't exist, we add them
ALTER TABLE system_locks ADD COLUMN status TEXT DEFAULT 'ACQUIRED';
ALTER TABLE system_locks ADD COLUMN released_at DATETIME;
