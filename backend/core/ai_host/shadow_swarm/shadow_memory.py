
import logging
import json
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class IncidentType(Enum):
    CONFLICT = "conflict"
    RESCUE = "rescue"
    ROLLBACK = "rollback"
    FAILURE = "failure"
    HIGH_FRICTION = "high_friction"

class TechnicalIncident(BaseModel):
    incident_id: str
    mission_id: str
    target_path: str
    target_layer: str
    incident_type: IncidentType
    description: str
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    resolution_applied: Optional[str] = None
    timestamp: datetime = datetime.now()

class ShadowMemoryManager:
    """
    Persists and retrieves historical technical incidents for the Shadow Swarm.
    Enables 'Historical Conflict Awareness'.
    """
    
    def __init__(self):
        self._ensure_table()

    def _ensure_table(self):
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS shadow_memory (
                            incident_id TEXT PRIMARY KEY,
                            mission_id TEXT,
                            target_path TEXT,
                            target_layer TEXT,
                            incident_type TEXT,
                            description TEXT,
                            severity TEXT,
                            resolution_applied TEXT,
                            timestamp TEXT
                        )
                    """)
                    # Indices for fast lookup
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_shadow_path ON shadow_memory(target_path)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_shadow_layer ON shadow_memory(target_layer)")
                    conn.commit()
        except Exception as e:
            logger.error(f"[SHADOW-MEMORY] Failed to ensure table: {e}")

    def record_incident(self, incident: TechnicalIncident):
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    query = """
                    INSERT INTO shadow_memory (
                        incident_id, mission_id, target_path, target_layer,
                        incident_type, description, severity, resolution_applied, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    conn.execute(query, (
                        incident.incident_id,
                        incident.mission_id,
                        incident.target_path,
                        incident.target_layer,
                        incident.incident_type.value,
                        incident.description,
                        incident.severity,
                        incident.resolution_applied,
                        incident.timestamp.isoformat()
                    ))
                    conn.commit()
                    logger.info(f"[SHADOW-MEMORY] Recorded {incident.incident_type.value} incident on {incident.target_path}")
        except Exception as e:
            logger.error(f"[SHADOW-MEMORY] Failed to record incident: {e}")

    def get_incidents(self, path: Optional[str] = None, layer: Optional[str] = None) -> List[TechnicalIncident]:
        incidents = []
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    query = "SELECT * FROM shadow_memory WHERE 1=1"
                    params = []
                    if path:
                        query += " AND target_path = ?"
                        params.append(path)
                    if layer:
                        query += " AND target_layer = ?"
                        params.append(layer)
                    
                    query += " ORDER BY timestamp DESC LIMIT 10"
                    
                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()
                    for row in rows:
                        incidents.append(TechnicalIncident(
                            incident_id=row["incident_id"],
                            mission_id=row["mission_id"],
                            target_path=row["target_path"],
                            target_layer=row["target_layer"],
                            incident_type=IncidentType(row["incident_type"]),
                            description=row["description"],
                            severity=row["severity"],
                            resolution_applied=row["resolution_applied"],
                            timestamp=datetime.fromisoformat(row["timestamp"])
                        ))
        except Exception as e:
            logger.error(f"[SHADOW-MEMORY] Failed to retrieve incidents: {e}")
        return incidents

shadow_memory_manager = ShadowMemoryManager()
