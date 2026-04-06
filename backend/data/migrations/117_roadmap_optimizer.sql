-- OMNIWEB — BLOQUE: GOVERNANCE STRATEGIC ROADMAP OPTIMIZER
-- Migración 117: Persistencia de secuencia taktika y prioritización estratégica.

CREATE TABLE IF NOT EXISTS governance_roadmap_optimizations (
    item_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL, -- ACTION_PACKAGE, MISSION, ADVISORY
    source_id TEXT NOT NULL,
    suggested_rank INTEGER,
    priority_band TEXT, -- EXECUTE_NOW, HIGH_PRIORITY_EXT, WAIT_FOR_PRECONDITIONS, DEFER_LOW_RETURN, CHAIN_AFTER_X, CREATOR_REVIEW_REQUIRED
    urgency_score REAL,
    expected_relief REAL,
    expected_cost REAL,
    dependency_refs TEXT, -- JSON list of other item_ids
    rationale TEXT,
    recommended_timing TEXT,
    blockers TEXT, -- JSON list of strings
    confidence REAL,
    creator_override_state TEXT DEFAULT 'NONE', -- FIXED, IGNORED, MOVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick lookup
CREATE INDEX IF NOT EXISTS idx_roadmap_rank ON governance_roadmap_optimizations(suggested_rank);
CREATE INDEX IF NOT EXISTS idx_roadmap_source ON governance_roadmap_optimizations(source_type, source_id);
