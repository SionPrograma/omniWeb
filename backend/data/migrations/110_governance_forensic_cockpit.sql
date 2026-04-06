-- OMNIWEB MIGRATION 110: GOVERNANCE FORENSIC COCKPIT INFRASTRUCTURE
-- Adds target domain and metadata to action traces for global dashboard aggregation.

ALTER TABLE governance_action_traces ADD COLUMN target_domain TEXT DEFAULT 'GLOBAL';
ALTER TABLE governance_action_traces ADD COLUMN metadata TEXT DEFAULT '{}';
ALTER TABLE governance_action_traces ADD COLUMN action_category TEXT DEFAULT 'TACTICAL'; -- TACTICAL, STRATEGIC, URGENT

-- Index for faster aggregation
CREATE INDEX IF NOT EXISTS idx_gov_trace_outcome ON governance_action_traces(outcome_status);
CREATE INDEX IF NOT EXISTS idx_gov_trace_domain ON governance_action_traces(target_domain);
