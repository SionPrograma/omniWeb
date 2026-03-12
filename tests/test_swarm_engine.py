import pytest
import asyncio
from backend.core.swarm_engine.swarm_controller import swarm_controller
from backend.core.swarm_engine.agent_registry import agent_registry
from backend.core.swarm_engine.swarm_models import AgentRole, AgentStatus
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

@pytest.mark.asyncio
async def test_swarm_agent_registration():
    agents = agent_registry.get_agents_by_role(AgentRole.KNOWLEDGE)
    assert len(agents) > 0
    assert agents[0].name == "Alpha-Know"

@pytest.mark.asyncio
async def test_swarm_task_orchestration():
    query = "Investiga los riesgos de ingeniería del puente de londres"
    result = await swarm_controller.execute_swarm_query(query)
    
    assert "Investigador" in result or "Respuesta de" in result
    assert "Alpha-Know" in result or "Beta-Res" in result or "Delta-Eng" in result

@pytest.mark.asyncio
async def test_agent_status_updates():
    agents = agent_registry.get_agents_by_role(AgentRole.RESEARCH)
    agent_id = agents[0].id
    agent_registry.update_status(agent_id, AgentStatus.BUSY)
    
    assert agent_registry.local_agents[agent_id].status == AgentStatus.BUSY
