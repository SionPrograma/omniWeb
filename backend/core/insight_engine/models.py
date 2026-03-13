from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class InsightType(str, Enum):
    PATTERN = "pattern"
    HEALTH = "health"
    SUGGESTION = "suggestion"
    ANOMALY = "anomaly"

class InsightSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ActionableInsight(BaseModel):
    id: str
    user_id: str
    type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    related_entries: List[str] = [] # List of entry_ids
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_actioned: bool = False
    metadata: Dict[str, Any] = {}

class InsightSummary(BaseModel):
    total_insights: int
    critical_count: int
    recent_insights: List[ActionableInsight]
