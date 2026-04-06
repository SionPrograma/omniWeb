
ALTER TABLE mission_handoffs ADD COLUMN ancestry_id TEXT;
-- Populate ancestry_id with handoff_id for current main missions as they are the root nodes
UPDATE mission_handoffs SET ancestry_id = handoff_id WHERE branch_id = 'main' AND ancestry_id IS NULL;
