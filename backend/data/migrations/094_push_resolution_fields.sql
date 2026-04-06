-- Fase 93: Adding resolvable context to atomic push sessions
ALTER TABLE atomic_push_sessions ADD COLUMN is_resolvable INTEGER DEFAULT 0;
ALTER TABLE atomic_push_sessions ADD COLUMN blocked_handoff_id TEXT;
