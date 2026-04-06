from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class AICommandResponse(BaseModel):
    intent: str
    status: str
    message: str
    payload: Dict[str, Any] = {}
    audit: Optional[Dict[str, Any]] = None
    hud: Optional[Dict[str, Any]] = None

class CommandProcessor(ABC):
    async def can_handle(self, command: str) -> bool:
        """Determines if this processor is qualified to handle the given command."""
        return False

    @abstractmethod
    async def process(self, msg: str) -> AICommandResponse:
        pass
