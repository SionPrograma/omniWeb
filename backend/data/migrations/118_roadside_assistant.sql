-- OMNIWEB — BLOQUE: GOVERNANCE TACTICAL ROADSIDE ASSISTANT
-- Migración 118: Monitoreo en vivo de ejecución de la secuencia táctica.

CREATE TABLE IF NOT EXISTS governance_roadside_events (
    event_id TEXT PRIMARY KEY,
    active_package_id TEXT,
    source_roadmap_item_id TEXT,
    event_type TEXT, -- PRECONDITION_BROKEN, ORDER_DEVIATION, NEW_PRESSURE_SPIKE, BLOCKER_DETECTED, PACKAGE_STALE, REPLAN_RECOMMENDED
    severity_band TEXT, -- INFO, WARNING, CRITICAL
    rationale TEXT,
    suggested_action TEXT,
    confidence REAL,
    is_dismissed BOOLEAN DEFAULT 0,
    creator_decision TEXT DEFAULT 'PENDING', -- IGNORED, ACCEPTED, RECALCULATED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_roadside_package ON governance_roadside_events(active_package_id);
CREATE INDEX IF NOT EXISTS idx_roadside_dismissed ON governance_roadside_events(is_dismissed);
