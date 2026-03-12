from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel

class AICommandResponse(BaseModel):
    intent: str
    status: str
    message: str
    payload: Dict[str, Any] = {}

class CommandProcessor(ABC):
    @abstractmethod
    async def process(self, msg: str) -> AICommandResponse:
        pass
