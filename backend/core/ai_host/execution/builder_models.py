import uuid
import time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class BuilderStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"

class BuilderModuleType(str, Enum):
    INITIALIZATION = "initialization"
    IMPLEMENTATION = "implementation"
    AUDIT = "audit"
    TESTING = "testing"
    REFACTORING = "refactoring"

class BuilderModule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    title: str
    description: Optional[str] = None
    status: BuilderStatus = BuilderStatus.PENDING
    progress: float = 0.0
    sequence_order: int
    module_type: BuilderModuleType = BuilderModuleType.IMPLEMENTATION
    payload: Dict[str, Any] = {}
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    last_update: float = Field(default_factory=time.time)
    current_submodule: Optional[str] = None

class BuilderTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    roadmap_id: str
    title: str
    status: BuilderStatus = BuilderStatus.PENDING
    progress: float = 0.0
    current_module_id: Optional[str] = None
    modules: List[BuilderModule] = []
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    last_update: float = Field(default_factory=time.time)
    current_submodule: Optional[str] = None
    metadata: Dict[str, Any] = {}
