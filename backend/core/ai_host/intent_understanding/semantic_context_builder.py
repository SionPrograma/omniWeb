import logging
from typing import Dict, Any, Optional
from .conversation_tracker import conversation_tracker
from ..cognition.cognitive_core import cognitive_core

logger = logging.getLogger(__name__)

class SemanticContext:
    def __init__(self, 
                 request: str, 
                 session_id: str, 
                 system_state: Dict[str, Any],
                 history: Any,
                 active_mission: Optional[str] = None):
        self.request = request
        self.session_id = session_id
        self.system_state = system_state
        self.history = history
        self.active_mission = active_mission

class SemanticContextBuilder:
    """
    Gather signals from history, system state, and active missions 
    to provide a rich background for intent detection.
    """
    
    async def build(self, request: str, session_id: str) -> SemanticContext:
        logger.debug(f"[CONTEXT_BUILDER] Building context for request: {request}")
        
        # 1. Get Session state
        session_ctx = conversation_tracker.get_context(session_id)
        
        # 2. Get World state
        ws = cognitive_core.world_state
        
        return SemanticContext(
            request=request,
            session_id=session_id,
            system_state=vars(ws),
            history=session_ctx,
            active_mission=session_ctx.last_mission_goal
        )

semantic_context_builder = SemanticContextBuilder()
