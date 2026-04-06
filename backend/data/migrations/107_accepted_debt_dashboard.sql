-- OMNIWEB MIGRATION 107: ACCEPTED DEBT DASHBOARD ENHANCEMENTS
-- Adds domain and detailed lifecycle metadata to risk overrides.

ALTER TABLE governance_risk_overrides ADD COLUMN affected_domain TEXT;
ALTER TABLE governance_risk_overrides ADD COLUMN oracle_pressure_delta REAL DEFAULT 0.0;
ALTER TABLE governance_risk_overrides ADD COLUMN stability_metrics TEXT; -- JSON metadata
ALTER TABLE governance_risk_overrides ADD COLUMN priority_rank INTEGER DEFAULT 0; -- Higher = more critical intervention
ALTER TABLE governance_risk_overrides ADD COLUMN source_advisory_id TEXT; -- Direct link to origin
