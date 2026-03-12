from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class TaskCategory(str, Enum):
    OPTIMIZATION = "optimization"
    LEARNING = "learning"
    EXPLORATION = "exploration"
    ARCHITECTURE = "architecture"
    SIMULATION = "simulation"
    GENERAL = "general"

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    AUDITING = "auditing"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    REPAIRING = "repairing"
    VERIFIED = "verified"
    FAILED = "failed"

class SuperCommandIntent(BaseModel):
    category: TaskCategory
    command: str
    target: Optional[str] = None
    complexity: float = 0.5 # 0.0 to 1.0

class ExecutionStep(BaseModel):
    id: int
    name: str
    action: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    details: Optional[str] = None

class SuperPrompt(BaseModel):
    task_id: str
    title: str
    category: TaskCategory
    description: str
    steps: List[ExecutionStep] = []
    current_step_id: int = 0
    overall_status: ExecutionStatus = ExecutionStatus.PENDING

class SuperCommandResult(BaseModel):
    task_id: str
    success: bool
    summary: str
    issues_detected: List[str] = []
    actions_performed: List[str] = []
    stability_verified: bool = False
    final_output: Optional[str] = None
