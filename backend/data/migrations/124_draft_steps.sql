-- OMNIWEB — BLOQUE: OMNI_CATALYST_SPEC_TRANSLATOR_V0.3
-- Migración 124: Refuerzo de Borradores con Pasos Sugeridos

ALTER TABLE governance_mission_auto_drafts ADD COLUMN suggested_steps TEXT;
ALTER TABLE governance_mission_auto_drafts ADD COLUMN catalyst_trace_id TEXT;
