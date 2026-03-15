from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class ReputationEdge(BaseModel):
    id: str
    source_user_id: str
    target_user_id: str
    interaction_type: str
    trust_score: float = 0.0
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}

class LeadershipInsight(BaseModel):
    id: str
    user_id: str
    insight_type: str = "leadership_detection"
    message: str
    status: str = "pending" # pending, approved, rejected, implemented
    recommender: str = "AI_Host"
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}
