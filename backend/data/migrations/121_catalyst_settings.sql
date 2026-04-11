-- OMNIWEB — BLOQUE: OMNI_CATALYST_SKILL_BRIDGE_V0.1
-- Migración 121: Configuración de Aceleradores (Catalysts)

INSERT OR IGNORE INTO governance_engine_parameters (param_id, engine_name, param_key, current_value, default_value, description)
VALUES ('CAT-001', 'ORCHESTRATION', 'CATALYST_ENABLED', 'true', 'true', 'Habilita el uso de catalizadores externos para aceleración táctica (Phase 121)');

INSERT OR IGNORE INTO governance_engine_parameters (param_id, engine_name, param_key, current_value, default_value, description)
VALUES ('CAT-002', 'ORCHESTRATION', 'CATALYST_FREEZE', 'false', 'false', 'Congela todas las llamadas a catalizadores inmediatamente');
