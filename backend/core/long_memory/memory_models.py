from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class MemoryEntry(BaseModel):
    id: Optional[int] = None
    memory_type: str # project_memory, workflow_memory, etc.
    title: str
    summary: str
    content: str
    source_chip: Optional[str] = None
    source_session: Optional[str] = None
    importance_score: float = 0.5
    confidence_score: float = 1.0
    created_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None

class MemoryLink(BaseModel):
    id: Optional[int] = None
    memory_id: int
    related_type: str # chip, workflow, project, etc.
    related_id: str
    relationship: str # used_in, created_by, related_to
    created_at: Optional[datetime] = None
