-- 115_mission_feedback_columns.sql
-- Agregamos columnas de métricas de fricción y cumplimiento de precondiciones a system_missions.

ALTER TABLE system_missions ADD COLUMN friction REAL DEFAULT 1.0;
ALTER TABLE system_missions ADD COLUMN preconditions_ok INTEGER DEFAULT 1; -- 1 = OK, 0 = FAIL
