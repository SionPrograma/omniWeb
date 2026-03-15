from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SuggestionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"

class AISuggestion(BaseModel):
    id: str
    suggestion_type: str
    content: Dict[str, Any]
    severity: str = "info"
    status: SuggestionStatus = SuggestionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)

class AdminOperation(BaseModel):
    admin_id: str
    operation_type: str
    target_resource: str
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

class SystemCheckpoint(BaseModel):
    id: Optional[int] = None
    creator_id: str
    label: str
    db_backup_path: str
    created_at: datetime = Field(default_factory=datetime.now)
