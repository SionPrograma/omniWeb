-- PHASE 113: WISDOM FEEDBACK TRACEABILITY & BRANCH FRICTION
-- Closing the loop between Atlas drafts and real outcomes.

-- 1. Roadmap Branch Enhancement
-- Track the draft that originated this branch and its baseline friction.
ALTER TABLE roadmap_branches ADD COLUMN source_draft_id TEXT;
ALTER TABLE roadmap_branches ADD COLUMN friction REAL DEFAULT 0;

-- 2. Mission Handoff (Proposed Missions) Enhancement
-- Ensure the intent of a draft carries over through the handoff phase.
ALTER TABLE mission_handoffs ADD COLUMN source_draft_id TEXT;

-- 3. System Missions (Active Tasks) Enhancement
-- Complete the chain by persisting the origin draft throughout execution.
ALTER TABLE system_missions ADD COLUMN source_draft_id TEXT;
