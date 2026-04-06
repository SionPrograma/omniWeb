-- Fase 92: Adding metadata column to handoffs for traceability
ALTER TABLE mission_handoffs ADD COLUMN metadata TEXT;
