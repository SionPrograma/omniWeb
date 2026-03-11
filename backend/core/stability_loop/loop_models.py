from enum import Enum
from pydantic import BaseModel
from typing import Optional, List, Any, Dict

class LoopStep(str, Enum):
    AUDIT = "AUDIT_SYSTEM"
    ANALYZE = "ANALYZE_TASK"
    PLAN = "PLAN_EXECUTION"
    EXECUTE = "APPLY_CHANGE"
    TEST = "RUN_TESTS"
    VERIFY = "VERIFY_STABILITY"
    REPAIR = "REPAIR"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    ROLLBACK = "ROLLBACK"

class TaskState(BaseModel):
    task_id: str
    current_step: LoopStep = LoopStep.AUDIT
    cycle_count: int = 0
    max_cycles: int = 5
    is_stable: bool = False
    errors: List[str] = []
    repair_attempts: int = 0
    history: List[Dict[str, Any]] = []

class TaskAnalytics(BaseModel):
    estimated_risk: float # 0.0 to 1.0
    impacted_services: List[str]
    requires_rollback_point: bool = True
