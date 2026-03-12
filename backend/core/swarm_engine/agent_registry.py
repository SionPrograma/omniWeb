import logging
from typing import Dict, List, Optional
from .swarm_models import SwarmAgentModel, AgentRole, AgentStatus

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Manages the lifecycle and location of swarm agents across the network."""
    
    def __init__(self):
        self.local_agents: Dict[str, SwarmAgentModel] = {}
        self.remote_agents: Dict[str, SwarmAgentModel] = {}

    def register_local_agent(self, agent: SwarmAgentModel):
        self.local_agents[agent.id] = agent
        logger.info(f"SwarmRegistry: Registered local agent {agent.name} [{agent.role}]")

    def register_remote_agent(self, agent: SwarmAgentModel):
        self.remote_agents[agent.id] = agent
        logger.info(f"SwarmRegistry: Discovered remote agent {agent.name} from node {agent.node_id}")

    def get_agents_by_role(self, role: AgentRole) -> List[SwarmAgentModel]:
        all_agents = list(self.local_agents.values()) + list(self.remote_agents.values())
        return [a for a in all_agents if a.role == role]

    def update_status(self, agent_id: str, status: AgentStatus):
        if agent_id in self.local_agents:
            self.local_agents[agent_id].status = status
        elif agent_id in self.remote_agents:
            self.remote_agents[agent_id].status = status

agent_registry = AgentRegistry()
