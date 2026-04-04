import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from .mission_models import MissionState, MissionStatus

logger = logging.getLogger(__name__)

class PriorityClass(str, Enum):
    URGENT = "URGENT"           # Immediate attention needed (CRITICAL / PIN_REQUIRED)
    HIGH = "HIGH"               # Ready and high value
    NORMAL = "NORMAL"           # Standard operations
    BACKGROUND = "BACKGROUND"   # Low priority or automatic tasks
    DEFERRED = "DEFERRED"       # Waiting for resources / locks

class ReadinessState(str, Enum):
    READY = "READY"                     # No blocks, ready to run
    WAITING_RESOURCE = "WAITING_RESOURCE" # Blocked by resource lock or dependency
    PAUSED_BY_GOVERNANCE = "PAUSED_BY_GOVERNANCE" # Risk limit or Cooldown
    BLOCKED_BY_ERROR = "BLOCKED_BY_ERROR" # Technical failure / NEEDS_REVIEW
    ARCHIVED = "ARCHIVED"               # Finished or superseded

class PriorityEngine:
    """
    Intelligent Mission Scheduler & Priority Engine.
    Evaluates system signals to recommend focus and execution order.
    """
    
    def calculate_mission_rank(self, mission: MissionState, is_focused: bool = False) -> Dict[str, Any]:
        """
        Calculates the real-time priority score and state for a mission.
        """
        score = 0.0
        p_class = PriorityClass.NORMAL
        readiness = ReadinessState.READY
        
        # 1. Base Status Evaluation
        if mission.status == MissionStatus.COMPLETED or mission.status == MissionStatus.ARCHIVED:
            return {"score": -100.0, "class": PriorityClass.BACKGROUND, "readiness": ReadinessState.ARCHIVED}
        
        if mission.status == MissionStatus.FAILED:
            return {"score": -50.0, "class": PriorityClass.DEFERRED, "readiness": ReadinessState.BLOCKED_BY_ERROR}

        # 2. Focus Signal
        if is_focused:
            score += 40.0 # High value because the creator is working on it
        
        # 3. Governance Signals (Bloques 6-9)
        params = mission.parameters
        if params.get("cooldown_active"):
            score += 10.0 # Needs attention to clear cooldown
            readiness = ReadinessState.PAUSED_BY_GOVERNANCE
        
        risk_budget = params.get("risk_budget", 10.0)
        risk_consumed = params.get("risk_consumed", 0.0)
        if risk_consumed >= risk_budget:
            score += 60.0 # CRITICAL: Needs Authority/PIN
            p_class = PriorityClass.URGENT
            readiness = ReadinessState.PAUSED_BY_GOVERNANCE
        
        if mission.status == MissionStatus.PAUSED and "PIN" in "".join(mission.blocked_reasons):
            score += 80.0 # HIGHEST: Waiting for creator PIN
            p_class = PriorityClass.URGENT
            readiness = ReadinessState.PAUSED_BY_GOVERNANCE

        # 4. Resource & Dependency Signals
        from .resource_lock_manager import resource_lock_manager
        # Check if it has active locks (actively working)
        active_locks = resource_lock_manager.get_locks_for_mission(mission.mission_id)
        if active_locks:
            score += 15.0
        
        # Check for conflicts
        # Re-evaluating conflict might be expensive if done too often, 
        # but let's check the readiness.
        if mission.status == MissionStatus.BLOCKED:
            if any("CONFLICT" in r for r in mission.blocked_reasons):
                readiness = ReadinessState.WAITING_RESOURCE
                score -= 10.0 # Lower priority while waiting for lock release
            else:
                readiness = ReadinessState.BLOCKED_BY_ERROR
        
        # 5. Goal Proximity / Evolution
        if mission.relation_type and ("RESCUE" in mission.relation_type or "REPAIR" in mission.relation_type):
            score += 20.0 # Fixes are generally more urgent
            
        # 6. Recency Bias (to prevent starvation, though subtle)
        days_old = (datetime.now() - mission.created_at).days
        score += min(5.0, days_old * 0.5)
        
        # Final Class determination if not already set
        if score >= 70: p_class = PriorityClass.URGENT
        elif score >= 40: p_class = PriorityClass.HIGH
        elif score >= 0: p_class = PriorityClass.NORMAL
        else: p_class = PriorityClass.BACKGROUND

        return {
            "score": round(score, 2),
            "class": p_class,
            "readiness": readiness
        }

    def rank_portfolio(self, missions: List[MissionState], focal_id: Optional[str] = None) -> List[MissionState]:
        """
        Sorts a list of missions by their calculated priority score.
        """
        for m in missions:
            rank = self.calculate_mission_rank(m, is_focused=(m.mission_id == focal_id))
            m.priority_score = rank["score"]
            m.priority_class = rank["class"].value
            m.readiness_state = rank["readiness"].value
        
        # Sort desc by score
        return sorted(missions, key=lambda x: x.priority_score, reverse=True)

priority_engine = PriorityEngine()
