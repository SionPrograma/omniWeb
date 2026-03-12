import logging
from typing import List, Dict, Optional
from .agent_models import AIAgent

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages external AI participants in the host environment."""
    
    def __init__(self):
        self.active_agents: Dict[str, AIAgent] = {}
        # Predefined "Expert" agents
        self.predefined = {
            "coder": {"name": "DevAI", "role": "Fullstack Developer"},
            "researcher": {"name": "Scout", "role": "Knowledge Discovery"},
            "creative": {"name": "Muse", "role": "Generative Assistant"}
        }

    def invite_agent(self, agent_type: str) -> Optional[AIAgent]:
        if agent_type in self.predefined:
            data = self.predefined[agent_type]
            agent = AIAgent(name=data["name"], role=data["role"])
            self.active_agents[agent.id] = agent
            logger.info(f"MultiAI: Invited agent {agent.name}")
            return agent
        return None

    def get_all_agents(self) -> List[AIAgent]:
        return list(self.active_agents.values())

    def update_agent_status(self, agent_id: str, status: str):
        if agent_id in self.active_agents:
            self.active_agents[agent_id].status = status

agent_manager = AgentManager()
