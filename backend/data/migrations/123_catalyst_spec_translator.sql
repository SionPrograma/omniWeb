-- OMNIWEB — BLOQUE: OMNI_CATALYST_SPEC_TRANSLATOR_V0.3
-- Migración 123: Configuración de Traducción de Especificaciones

INSERT OR IGNORE INTO governance_engine_parameters (param_id, engine_name, param_key, current_value, default_value, description)
VALUES ('CAT-004', 'ORCHESTRATION', 'CATALYST_SPEC_TRANSLATION_ENABLED', 'true', 'true', 'Habilita la traducción de intenciones a pasos de misión estructurados (Phase 123)');
