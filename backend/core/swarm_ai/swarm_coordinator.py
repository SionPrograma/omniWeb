from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime

class SwarmAgent(BaseModel):
    id: str
    role: str
    status: str = "idle"
    current_task: Optional[str] = None

class SwarmCoordinator:
    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}

    def register_agent(self, agent: SwarmAgent):
        self.agents[agent.id] = agent
        return agent

    def dispatch_task(self, task_description: str):
        """Dispatches a task to the most suitable idle agent in the swarm."""
        for agent in self.agents.values():
            if agent.status == "idle":
                agent.status = "working"
                agent.current_task = task_description
                return {"status": "dispatched", "agent_id": agent.id}
        return {"status": "busy", "message": "All agents are currently occupied."}

swarm_coordinator = SwarmCoordinator()
