from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time

class IdeaCluster(BaseModel):
    name: str # e.g. "Quantum Computing Basics"
    ideas_count: int
    related_topics: List[str]
    convergence_score: float # 0 to 1
    detected_at: float = Field(default_factory=time.time)

class ChipBlueprint(BaseModel):
    name: str
    description: str
    required_capabilities: List[str]
    complexity_estimate: str # "low", "medium", "high"
    evolution_path: List[str] = [] # List of parent ideas
