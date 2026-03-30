import json
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class MissionStatus(str, Enum):
    OPEN = "OPEN"           # Active mission
    PAUSED = "PAUSED"       # Human interrupted or switched context
    BLOCKED = "BLOCKED"     # Stuck on an issue or verification failure
    COMPLETED = "COMPLETED" # Mission objective reached
    FAILED = "FAILED"       # Critical error or goal unreachable

class MissionState(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    mission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active_goal: str
    status: MissionStatus = MissionStatus.OPEN
    plan_id: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    blocked_reasons: List[str] = Field(default_factory=list)
    related_targets: List[str] = Field(default_factory=list)
    context_snap: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class MissionManager:
    """
    Surgical Layer for Mission Memory Persistence.
    Ensures OmniWeb never forgets its technical goals.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MissionManager, cls).__new__(cls)
            cls._instance.active_mission = None
        return cls._instance

    def create_mission(self, goal: str, plan_id: str = None, pending_steps: List[str] = None, plan: Optional[Any] = None) -> MissionState:
        """
        Initializes a new mission and persists it.
        """
        snap = {}
        if plan:
            # Serializamos el plan para persistencia si es un objeto TaskPlan
            if hasattr(plan, 'model_dump'):
                snap["plan_data"] = plan.model_dump(mode='json')
            elif hasattr(plan, 'to_dict'):
                snap["plan_data"] = plan.to_dict()
            else:
                snap["plan_data"] = str(plan)

        mission = MissionState(
            active_goal=goal,
            plan_id=plan_id,
            pending_steps=pending_steps or [],
            context_snap=snap
        )
        self.save_mission(mission)
        self.active_mission = mission
        logger.info(f"[MISSION_MANAGER] New Mission Created: {mission.mission_id} - {goal}")
        return mission

    def save_mission(self, mission: MissionState):
        """
        Persists mission state to SQLite.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                query = """
                INSERT OR REPLACE INTO system_missions (
                    mission_id, active_goal, status, plan_id, 
                    completed_steps, pending_steps, blocked_reasons, 
                    related_targets, context_snap, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                conn.execute(query, (
                    mission.mission_id,
                    mission.active_goal,
                    mission.status.value,
                    mission.plan_id,
                    json.dumps(mission.completed_steps),
                    json.dumps(mission.pending_steps),
                    json.dumps(mission.blocked_reasons),
                    json.dumps(mission.related_targets),
                    json.dumps(mission.context_snap),
                    datetime.now().isoformat()
                ))
                conn.commit()

    def get_active_mission(self) -> Optional[MissionState]:
        """
        Retrieves the latest OPEN or PAUSED mission.
        """
        if self.active_mission and self.active_mission.status in [MissionStatus.OPEN, MissionStatus.PAUSED]:
            return self.active_mission

        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    row = conn.execute(
                        "SELECT * FROM system_missions WHERE status IN ('OPEN', 'PAUSED') ORDER BY updated_at DESC LIMIT 1"
                    ).fetchone()
                    
                    if row:
                        mission = self._row_to_mission(row)
                        self.active_mission = mission
                        return mission
            except Exception as e:
                logger.error(f"[MISSION_MANAGER] Error loading active mission: {e}")
        return None

    def update_mission_step(self, completed_step: str):
        """
        Moves a step from pending to completed.
        """
        mission = self.get_active_mission()
        if not mission: return

        if completed_step in mission.pending_steps:
            mission.pending_steps.remove(completed_step)
        
        if completed_step not in mission.completed_steps:
            mission.completed_steps.append(completed_step)
            
        mission.updated_at = datetime.now()
        
        if not mission.pending_steps:
            mission.status = MissionStatus.COMPLETED
            logger.info(f"[MISSION_MANAGER] Mission COMPLETED: {mission.mission_id}")
        
        self.save_mission(mission)

    def set_status(self, status: MissionStatus, reason: str = None):
        """
        Updates mission status significantly.
        """
        mission = self.get_active_mission()
        if not mission: return

        if mission.status == status and not reason: return
        mission.status = status
        if reason:
            mission.blocked_reasons.append(reason)
        
        mission.updated_at = datetime.now()
        self.save_mission(mission)
        logger.info(f"[MISSION_MANAGER] Mission {mission.mission_id} status changed to {status.value}")

    def _row_to_mission(self, row) -> MissionState:
        # Handle created_at and updated_at being either strings or datetime objects (sqlite3 vs mock)
        created_at = row['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except:
                created_at = datetime.now()
        
        updated_at = row['updated_at']
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except:
                updated_at = datetime.now()

        return MissionState(
            mission_id=row['mission_id'],
            active_goal=row['active_goal'],
            status=MissionStatus(row['status']),
            plan_id=row['plan_id'],
            completed_steps=json.loads(row['completed_steps'] or '[]'),
            pending_steps=json.loads(row['pending_steps'] or '[]'),
            blocked_reasons=json.loads(row['blocked_reasons'] or '[]'),
            related_targets=json.loads(row['related_targets'] or '[]'),
            context_snap=json.loads(row['context_snap'] or '{}'),
            created_at=created_at,
            updated_at=updated_at
        )

mission_manager = MissionManager()
