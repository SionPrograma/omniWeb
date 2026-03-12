import logging
import asyncio
from typing import List, Dict, Any
from .swarm_models import SwarmTask, TaskResult, AgentRole
from .agent_registry import agent_registry

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """Decomposes user intent into agent tasks and merges their outputs."""
    
    async def orchestrate(self, instruction: str) -> str:
        # Simple decomposition for Phase AD
        roles_needed = self._decompose(instruction)
        tasks = []
        
        for role in roles_needed:
            agents = agent_registry.get_agents_by_role(role)
            if agents:
                task = SwarmTask(instruction=instruction, required_roles=[role])
                tasks.append(self._delegate(task, agents[0]))

        # Wait for agents (Simulated async)
        results = await asyncio.gather(*tasks)
        return self._merge(results)

    def _decompose(self, instruction: str) -> List[AgentRole]:
        roles = []
        msg = instruction.lower()
        if "investig" in msg or "research" in msg: roles.append(AgentRole.RESEARCH)
        if "conoc" in msg or "know" in msg: roles.append(AgentRole.KNOWLEDGE)
        if "educ" in msg or "learn" in msg or "aprender" in msg: roles.append(AgentRole.EDUCATION)
        if "cod" in msg or "ingenier" in msg or "engine" in msg: roles.append(AgentRole.ENGINEERING)
        if "oportun" in msg or "trabaj" in msg or "job" in msg: roles.append(AgentRole.OPPORTUNITY)
        
        # Default to coordination if none detected
        if not roles: roles.append(AgentRole.COORDINATION)
        return roles

    async def _delegate(self, task: SwarmTask, agent: Any) -> TaskResult:
        logger.info(f"SwarmOrchestrator: Delegating to {agent.name}")
        # In a real swarm, this would go through the Event Bus or direct call
        # Here we simulate the agent processing
        await asyncio.sleep(0.1)
        return TaskResult(
            task_id=task.id,
            agent_id=agent.id,
            content=f"Respuesta de {agent.name} sobre: {task.instruction[:20]}..."
        )

    def _merge(self, results: List[TaskResult]) -> str:
        if not results: return "El enjambre no ha podido procesar la solicitud."
        
        merged = "Análisis del Enjambre OmniWeb:\n"
        for res in results:
            merged += f"• {res.content}\n"
        return merged

task_orchestrator = TaskOrchestrator()
