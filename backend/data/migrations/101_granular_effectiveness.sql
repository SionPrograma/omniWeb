-- OMNIWEB MIGRATION 101: GRANULAR EFFECTIVENESS
-- Adds persona-level tracking to the effectiveness audits.

ALTER TABLE compensation_effectiveness_audits ADD COLUMN persona_deltas TEXT;
