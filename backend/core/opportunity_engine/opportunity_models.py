from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class MarketDemand(BaseModel):
    skill_name: str
    demand_level: float # 0.0 to 1.0
    trending: bool
    salary_range: Optional[str] = None

class Opportunity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    type: str # "learning_project", "internship", "job", "collaboration"
    description: str
    required_skills: List[str]
    match_score: float = 0.0
    source: str # "internal", "distributed_network", "external"
    url: Optional[str] = None

class CareerPath(BaseModel):
    goal: str
    steps: List[Dict[str, Any]] # sequence of skills and opportunities
    estimated_time_months: int
