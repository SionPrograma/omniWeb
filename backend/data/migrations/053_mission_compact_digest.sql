-- Phase 53: Mission Context Compactor
-- Persistence for compact operational digests to improve focus-switching

ALTER TABLE system_missions ADD COLUMN compact_digest TEXT; -- JSON blob of MissionCompactDigest
