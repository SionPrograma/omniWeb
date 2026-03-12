from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class SkillVerification(BaseModel):
    skill_name: str
    verified_level: float
    verifier_id: str = "omniweb_ai_host"
    verification_method: str # "project", "exam", "simulation"
    timestamp: datetime = Field(default_factory=datetime.now)

class Certification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    level: str # "Foundation", "Professional", "Expert"
    user_id: str
    skills_covered: List[str]
    issue_date: datetime = Field(default_factory=datetime.now)
    verified: bool = True
    metadata: Dict[str, Any] = {}
