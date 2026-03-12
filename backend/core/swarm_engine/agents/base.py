from abc import ABC, abstractmethod
from typing import Dict, Any
from ..swarm_models import AgentRole

class SwarmAgent(ABC):
    def __init__(self, name: str, role: AgentRole):
        self.name = name
        self.role = role

    @abstractmethod
    async def process_task(self, instruction: str, data: Dict[str, Any]) -> str:
        pass
