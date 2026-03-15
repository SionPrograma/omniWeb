from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class UserMemoryMilestone(BaseModel):
    id: str
    user_id: str
    milestone_type: str
    description: Optional[str] = None
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}
