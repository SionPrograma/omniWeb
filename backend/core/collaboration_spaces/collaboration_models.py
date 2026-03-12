from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from backend.core.knowledge_domains.domain_models import DomainCategory

class ResearchNote(BaseModel):
    id: str
    author_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    linked_concepts: List[str] = []

class CollabProject(BaseModel):
    id: str
    title: str
    description: str
    domain: DomainCategory
    creator_id: str
    participants: List[str] = []
    notes: List[ResearchNote] = []
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)

class ProjectDiscussion(BaseModel):
    project_id: str
    messages: List[dict] = []
