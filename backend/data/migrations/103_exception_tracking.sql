-- OMNIWEB MIGRATION 103: EXCEPTION TRACKING
-- Adds state tracking for constitutional overrides and conditions.

ALTER TABLE branch_arbitrations ADD COLUMN compliance_state TEXT DEFAULT 'PENDING'; -- PENDING, FULFILLED, BREACHED, DEGRADED
ALTER TABLE branch_arbitrations ADD COLUMN resolved_at TIMESTAMP;
ALTER TABLE branch_arbitrations ADD COLUMN debt_level REAL DEFAULT 1.0; -- 0.0 to 1.0 impact
