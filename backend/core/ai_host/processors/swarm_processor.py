import logging
from typing import Dict, Any
from backend.core.swarm_engine.swarm_controller import swarm_controller
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class SwarmProcessor(CommandProcessor):
    """Bridges AI Host commands to the Autonomous Multi-Agent Swarm."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        result = await swarm_controller.execute_swarm_query(msg)
        
        return AICommandResponse(
            intent="swarm_execution",
            message=result,
            status="success",
            payload={"is_swarm": True}
        )

swarm_processor = SwarmProcessor()
