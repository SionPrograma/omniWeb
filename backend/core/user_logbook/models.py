from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

class UserEntryType(str, Enum):
    IDEA = "idea"
    TASK = "task"
    NOTE = "note"
    SYSTEM_EVENT = "system_event"
    CHIP_EVENT = "chip_event"

class UserLogbookEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    entry_type: UserEntryType
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class LogbookSearch(BaseModel):
    query: Optional[str] = None
    entry_type: Optional[UserEntryType] = None
    limit: int = 50
