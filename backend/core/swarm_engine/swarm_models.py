from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import time

class AgentRole(str, Enum):
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    EDUCATION = "education"
    ENGINEERING = "engineering"
    OPPORTUNITY = "opportunity"
    COORDINATION = "coordination"

class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"

class SwarmAgentModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: AgentRole
    status: AgentStatus = AgentStatus.IDLE
    node_id: str = "local"
    capabilities: List[str] = []

class SwarmTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instruction: str
    required_roles: List[AgentRole]
    payload: Dict[str, Any] = {}
    timestamp: float = Field(default_factory=time.time)
    status: str = "pending" # pending, in_progress, completed, failed

class TaskResult(BaseModel):
    task_id: str
    agent_id: str
    content: str
    data: Dict[str, Any] = {}
    confidence: float = 1.0
