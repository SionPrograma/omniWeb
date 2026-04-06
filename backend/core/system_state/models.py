from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class SystemHealth(str, Enum):
    HEALTHY = "healthy"
    UNVERIFIED = "unverified"
    UNKNOWN = "unknown"
    WARNING = "warning"
    ERROR = "error"
    DEACTIVATED = "deactivated"

class SystemMode(str, Enum):
    LIVE = "live"
    MAINTENANCE_PENDING = "maintenance_pending"
    READ_ONLY = "read_only"
    MAINTENANCE_ACTIVE = "maintenance_active"
    LOCKDOWN = "lockdown"

class ChipState(BaseModel):
    slug: str
    name: str
    status: str
    health: SystemHealth
    last_execution: Optional[str] = "never"
    metadata: Dict[str, Any] = {}

class SystemState(BaseModel):
    version: str
    system_mode: SystemMode = SystemMode.LIVE
    maintenance_info: Optional[Dict[str, Any]] = None
    announcement: Optional[Dict[str, Any]] = None
    git_branch: str
    git_commit: str
    health: SystemHealth
    ai_host: Dict[str, Any]
    database: Dict[str, Any]
    chips: List[ChipState]
    auditor_summary: Optional[Dict[str, Any]] = None
    pending_fixes: int = 0
    is_healing: bool = False
    memory_usage: Dict[str, Any] = {}
    flow_data: Dict[str, Any] = {}
    timestamp: Any
    uptime_seconds: float
    sync_status: Optional[Dict[str, Any]] = None
    cluster: Optional[Dict[str, Any]] = None
    active_mission: Optional[Dict[str, Any]] = None
    last_handoff: Optional[Dict[str, Any]] = None
    mission_hierarchy: Optional[Dict[str, Any]] = None # New for Phase 21: Mission Graph
    parallel_missions: List[Dict[str, Any]] = [] # Block 21: Focus/Parallelism
    proposals: List[Dict[str, Any]] = [] # Block 30: Swarm Visibility
    resource_locks: List[Dict[str, Any]] = [] # MISSION CONFLICT RESOLVER
    archived_missions: List[Dict[str, Any]] = [] # MISSION PORTFOLIO
    completed_missions: List[Dict[str, Any]] = [] # MISSION PORTFOLIO
    mission_events: List[Dict[str, Any]] = [] # MISSION CRITICAL TELEMETRY
    portfolio_pulse: List[Dict[str, Any]] = [] # MISSION CRITICAL TELEMETRY
    recommended_focus: Optional[Dict[str, Any]] = None # Phase 22: Mission Scheduling
    schedules: List[Dict[str, Any]] = [] # Block: MULTI-MISSION SCHEDULER
