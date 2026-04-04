-- Migration 051: Telemetry Attribution for Governance & Audit
-- Adds source_actor and source_chip to system_mission_telemetry

ALTER TABLE system_mission_telemetry ADD COLUMN source_actor TEXT; -- Agent, Shadow, Manager, etc.
ALTER TABLE system_mission_telemetry ADD COLUMN source_chip TEXT; -- chip-reparto, chip-finanzas, etc.
