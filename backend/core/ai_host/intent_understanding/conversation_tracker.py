import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SessionContext(BaseModel):
    last_topic: Optional[str] = None
    last_intent: Optional[str] = None
    last_mission_goal: Optional[str] = None
    active_swarm_id: Optional[str] = None
    recent_messages: List[str] = []
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.now()

class ConversationTracker:
    """
    Maintains the short-term semantic state of the conversation.
    Essential for interpreting short snippets like 'y ahora?' or 'seguimos'.
    """
    def __init__(self):
        self.sessions: Dict[str, SessionContext] = {}

    def get_context(self, session_id: str) -> SessionContext:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionContext()
        return self.sessions[session_id]

    def update_context(self, session_id: str, message: str, intent: str, topic: Optional[str] = None):
        ctx = self.get_context(session_id)
        ctx.last_intent = intent
        ctx.recent_messages.append(message)
        if len(ctx.recent_messages) > 10:
            ctx.recent_messages.pop(0)
        
        if topic:
            ctx.last_topic = topic
            
        ctx.timestamp = datetime.now()
        logger.debug(f"[TRACKER] Updated context for {session_id}: {intent} | {topic}")

    def set_mission(self, session_id: str, goal: str, swarm_id: Optional[str] = None):
        ctx = self.get_context(session_id)
        ctx.last_mission_goal = goal
        ctx.active_swarm_id = swarm_id
        ctx.last_topic = goal
        logger.info(f"[TRACKER] Context set to Mission: {goal}")

conversation_tracker = ConversationTracker()
