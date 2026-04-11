-- OMNIWEB — BLOQUE: OMNI_CATALYST_MEMORY_BRIDGE_V0.2
-- Migración 122: Configuración del Puente de Memoria Técnica

INSERT OR IGNORE INTO governance_engine_parameters (param_id, engine_name, param_key, current_value, default_value, description)
VALUES ('CAT-003', 'ORCHESTRATION', 'CATALYST_MEMORY_BRIDGE_ENABLED', 'false', 'false', 'Habilita el puente de lectura de memoria técnica para catalizadores (Phase 122)');
