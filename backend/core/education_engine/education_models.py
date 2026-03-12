from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class LearningStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    concepts: List[str] = []
    status: str = "pending" # pending, in_progress, completed
    mastery_score: float = 0.0

class LearningPath(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    target_skill_level: int = 1 # 1-5
    steps: List[LearningStep] = []
    created_at: datetime = Field(default_factory=datetime.now)
    completed: bool = False

class ConceptNode(BaseModel):
    id: str
    name: str
    children: List['ConceptNode'] = []

class UserSkill(BaseModel):
    concept: str
    level: float # 0.0 to 1.0
    experience_points: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)

class Certification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    user_id: str
    issue_date: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}
    verified: bool = True
