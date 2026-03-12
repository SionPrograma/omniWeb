import logging
from .agent_models import AgentInteraction

logger = logging.getLogger(__name__)

class ConversationRouter:
    """Orchestrates dialogue between multiple agents and the user."""
    
    def route_to_agent(self, message: str, target_agent_id: str):
        """Dispatches a user message to a specific specialist agent."""
        logger.info(f"ConvRouter: Routing message to {target_agent_id}")
        # In Phase AB, this is a conceptual bridge to future LLM integration
        return f"Message routed to {target_agent_id}"

conversation_router = ConversationRouter()
