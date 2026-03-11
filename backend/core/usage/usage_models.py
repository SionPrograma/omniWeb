from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class UsageEvent(BaseModel):
    event_type: str
    chip_slug: Optional[str] = None
    user_session: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.utcnow()
