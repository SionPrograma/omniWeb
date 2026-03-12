from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class CognitiveMetric(BaseModel):
    name: str # e.g., "logical_reasoning", "creativity"
    score: float # 0.0 to 1.0
    confidence: float # 0.0 to 1.0
    last_detected: datetime = Field(default_factory=datetime.now)

class SkillPattern(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_name: str
    strength: float
    frequency: int
    context_type: str # "coding", "logic", "explanation", "simulation"

class SkillProfile(BaseModel):
    user_id: str
    cognitive_metrics: Dict[str, CognitiveMetric] = {}
    top_skills: List[str] = []
    learning_speed: float = 0.5
    last_analysis: datetime = Field(default_factory=datetime.now)
