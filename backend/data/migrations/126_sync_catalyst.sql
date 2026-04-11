-- OMNIWEB — BLOQUE: GOVERNANCE POST-MISSION WISDOM SYNC
-- Migración 126: Integración con Catalyst Trace

ALTER TABLE governance_post_mission_syncs ADD COLUMN catalyst_trace_id TEXT;
