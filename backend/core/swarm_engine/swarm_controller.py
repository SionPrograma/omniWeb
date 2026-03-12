import logging
from typing import Optional
from .swarm_models import SwarmAgentModel, AgentRole
from .agent_registry import agent_registry
from .task_orchestrator import task_orchestrator

logger = logging.getLogger(__name__)

class SwarmController:
    """The central hub for multi-agent swarm operations."""
    
    def __init__(self):
        self._initialize_default_swarm()

    def _initialize_default_swarm(self):
        # Create local specialists
        specialists = [
            ("Alpha-Know", AgentRole.KNOWLEDGE),
            ("Beta-Res", AgentRole.RESEARCH),
            ("Gamma-Edu", AgentRole.EDUCATION),
            ("Delta-Eng", AgentRole.ENGINEERING),
            ("Epsilon-Opp", AgentRole.OPPORTUNITY)
        ]
        
        for name, role in specialists:
            agent = SwarmAgentModel(name=name, role=role)
            agent_registry.register_local_agent(agent)

    async def execute_swarm_query(self, query: str) -> str:
        logger.info(f"SwarmController: Activating swarm for: {query}")
        return await task_orchestrator.orchestrate(query)

swarm_controller = SwarmController()
