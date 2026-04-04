-- Migration: Create Mission Telemetry table
CREATE TABLE IF NOT EXISTS system_mission_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    step_id TEXT,
    event_type TEXT NOT NULL, -- mission_started, step_started, step_completed, warning, error, etc.
    severity TEXT DEFAULT 'INFO', -- INFO, WARNING, ERROR, CRITICAL
    message TEXT NOT NULL,
    details TEXT, -- JSON payload with extra context
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(mission_id) REFERENCES system_missions(mission_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mission_telemetry_id ON system_mission_telemetry(mission_id);
