import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class TelemetryEvent(BaseModel):
    mission_id: str
    step_id: Optional[str] = None
    event_type: str
    severity: str = "INFO"
    message: str
    source_actor: Optional[str] = "system" # New for AUDIT OVERLAY
    source_chip: Optional[str] = None      # New for AUDIT OVERLAY
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class MissionTelemetryManager:
    """
    Surgical Telemetry Layer for OmniWeb Missions.
    Handles real-time operational event logging.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MissionTelemetryManager, cls).__new__(cls)
        return cls._instance

    def record_event(self, mission_id: str, event_type: str, message: str, severity: str = "INFO", step_id: str = None, details: Dict[str, Any] = None, source_actor: str = "system", source_chip: str = None):
        """
        Records an operational event in the telemetry log.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                query = """
                INSERT INTO system_mission_telemetry (
                    mission_id, step_id, event_type, severity, message, details, source_actor, source_chip
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                conn.execute(query, (
                    mission_id,
                    step_id,
                    event_type,
                    severity,
                    message,
                    json.dumps(details) if details else "{}",
                    source_actor,
                    source_chip
                ))
                conn.commit()
                logger.info(f"[MISSION_TELEMETRY] Mission {mission_id}: {event_type} - {message} [Actor: {source_actor}]")

    def get_recent_events(self, mission_id: str, limit: int = 20) -> List[TelemetryEvent]:
        """
        Retrieves recent events for a specific mission.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM system_mission_telemetry WHERE mission_id = ? ORDER BY timestamp DESC LIMIT ?", 
                    (mission_id, limit)
                ).fetchall()
                
                events = []
                for row in rows:
                    details = {}
                    try: details = json.loads(row['details']) if row['details'] else {}
                    except: pass
                    
                    # Convert timestamp handle sqlite date string vs datetime
                    ts = row['timestamp']
                    if isinstance(ts, str):
                        try: ts = datetime.fromisoformat(ts.replace(' ', 'T'))
                        except: ts = datetime.now()

                    events.append(TelemetryEvent(
                        mission_id=row['mission_id'],
                        step_id=row['step_id'],
                        event_type=row['event_type'],
                        severity=row['severity'],
                        message=row['message'],
                        source_actor=row['source_actor'] if 'source_actor' in row.keys() else "system",
                        source_chip=row['source_chip'] if 'source_chip' in row.keys() else None,
                        details=details,
                        timestamp=ts
                    ))
                return events

    def get_portfolio_pulse(self, limit: int = 15) -> List[TelemetryEvent]:
        """
        Aggregates critical events across all missions for a global 'pulse'.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM system_mission_telemetry ORDER BY timestamp DESC LIMIT ?", 
                    (limit,)
                ).fetchall()
                
                events = []
                for row in rows:
                    details = {}
                    try: details = json.loads(row['details']) if row['details'] else {}
                    except: pass

                    ts = row['timestamp']
                    if isinstance(ts, str):
                        try: ts = datetime.fromisoformat(ts.replace(' ', 'T'))
                        except: ts = datetime.now()

                    events.append(TelemetryEvent(
                        mission_id=row['mission_id'],
                        step_id=row['step_id'],
                        event_type=row['event_type'],
                        severity=row['severity'],
                        message=row['message'],
                        source_actor=row['source_actor'] if 'source_actor' in row.keys() else "system",
                        source_chip=row['source_chip'] if 'source_chip' in row.keys() else None,
                        details=details,
                        timestamp=ts
                    ))
                return events

mission_telemetry = MissionTelemetryManager()
