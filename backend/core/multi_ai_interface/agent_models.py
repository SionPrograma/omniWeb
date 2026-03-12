from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

class AIAgent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str
    icon_url: Optional[str] = None
    status: str = "idle" # "idle", "speaking", "thinking"
    last_message: Optional[str] = None
    position: Dict[str, int] = {"x": 100, "y": 100}

class AgentInteraction(BaseModel):
    agent_id: str
    message: str
    timestamp: float
