from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

class EntryType(str, Enum):
    IDEA = "idea"
    BUG = "bug"
    FIX = "fix"
    TEST = "test"
    DECISION = "decision"
    TASK = "task"
    NOTE = "note"
    ARCHITECTURE = "architecture"
    RELEASE = "release"
    AUDIT = "audit"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EntryStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    DONE = "done"

class MasterLogbookEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: EntryType
    content: str
    priority: Priority = Priority.MEDIUM
    chip_reference: Optional[str] = None
    status: EntryStatus = EntryStatus.OPEN
    author_role: str = "creator"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

class MasterLogbookFilter(BaseModel):
    type: Optional[EntryType] = None
    priority: Optional[Priority] = None
    status: Optional[EntryStatus] = None
    chip_reference: Optional[str] = None
