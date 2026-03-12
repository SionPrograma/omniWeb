from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
import time

class Opportunity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    type: str # "project", "job", "collaboration", "learning"
    description: str
    required_skills: List[str]
    reward: Optional[str] = None
    scarcity_index: float = 0.5 # 0 to 1, how rare this skill combination is
    location: str = "remote"
    node_source: str = "local"

class SkillDemand(BaseModel):
    skill_name: str
    demand_level: float # 0 to 1
    growth_rate: float
    avg_reward: str

class TalentProfile(BaseModel):
    user_id: str
    skills: List[str]
    availability: bool = True
    reputation: float = 1.0
