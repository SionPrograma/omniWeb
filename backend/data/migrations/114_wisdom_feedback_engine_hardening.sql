-- 114_wisdom_feedback_engine_hardening.sql
-- Completa el modelo de datos para el motor de comparación de sabiduría táctica.

-- Eliminar si existe para recrear con el esquema exacto solicitado (o usar ALTER TABLE si es crítico mantener datos previos, pero en este punto de desarrollo la recreación es más limpia para consistencia)
DROP TABLE IF EXISTS governance_wisdom_feedback;

CREATE TABLE governance_wisdom_feedback (
    feedback_id TEXT PRIMARY KEY,
    source_atlas_node_ref TEXT,
    source_draft_ref TEXT,
    resulting_mission_ref TEXT, -- mission_id
    resulting_branch_ref TEXT,  -- branch_id (Phase 97+)
    predicted_intent TEXT,      -- Qué se esperaba lograr (del draft)
    actual_outcome_summary TEXT, -- Resumen del resultado real (de la autopsia o misión)
    preconditions_respected INTEGER DEFAULT 1, -- 1 = Sí, 0 = No
    feedback_state TEXT,        -- WISDOM_CONFIRMED, WISDOM_PARTIALLY_CONFIRMED, WISDOM_CONTRADICTED, DRAFT_MISAPPLIED, INSUFFICIENT_OUTCOME_SIGNAL
    rationale TEXT,             -- Explicación técnica del veredicto
    supporting_refs TEXT,       -- JSON con links a trazas, autopsias o logs
    proposed_confidence_delta REAL DEFAULT 0,
    proposed_reusability_delta REAL DEFAULT 0,
    creator_decision TEXT DEFAULT 'PENDING', -- PENDING, APPLIED, REJECTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas rápidas
CREATE INDEX idx_wisdom_feedback_draft ON governance_wisdom_feedback(source_draft_ref);
CREATE INDEX idx_wisdom_feedback_mission ON governance_wisdom_feedback(resulting_mission_ref);
