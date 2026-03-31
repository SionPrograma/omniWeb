import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SessionContext(BaseModel):
    last_topic: Optional[str] = None
    last_intent: Optional[str] = None
    last_mission_goal: Optional[str] = None
    last_referenced_entity: Optional[str] = None # For 'eso', 'este'
    active_panel_id: Optional[str] = None # For 'ese panel', 'acá'
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
        self._hydrate_from_semantic_memory()

    def _hydrate_from_semantic_memory(self):
        """Restores working memory thread from persistent semantic disk buffer on server reboot."""
        try:
            from ..memory.semantic_memory import semantic_memory
            if semantic_memory.buffer:
                ctx = SessionContext()
                
                # Retrieve last explicit intent and topic
                ctx.last_intent = semantic_memory.get_last_intent()
                ctx.last_topic = semantic_memory.get_last_topic()
                
                # Recover recent dialog buffer for 'Working Memory'
                for item in list(semantic_memory.buffer)[-10:]:
                    if 'prompt' in item:
                        ctx.recent_messages.append(item['prompt'])
                
                # Reconstruct 'Mission Context' if the last interaction was an executive command
                if ctx.last_intent in ["BUILD_INTENT", "REMEDIATION_INTENT", "SYSTEM_AUDIT_INTENT"]:
                    ctx.last_mission_goal = ctx.last_topic
                    
                self.sessions["default_user"] = ctx
                logger.info("[TRACKER] Working Memory successfully hydrated from persistent layer.")
        except Exception as e:
            logger.warning(f"[TRACKER] Could not hydrate from persistent memory: {e}")

    def get_context(self, session_id: str) -> SessionContext:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionContext()
        return self.sessions[session_id]

    def update_context(self, session_id: str, message: str, intent: str, topic: Optional[str] = None):
        print(f"DEBUG: [TRACKER] update_context called for {session_id} with msg: '{message}'")
        ctx = self.get_context(session_id)
        ctx.last_intent = intent
        ctx.recent_messages.append(message)
        if len(ctx.recent_messages) > 10:
            ctx.recent_messages.pop(0)
        
        # ENTITY SCANNING (Identify what the user is talking about right now)
        msg_lower = message.lower()
        entities = ["chip-finanzas", "chip-reparto", "chip-idiomas", "logbook", "context-panel", "system inspection", "dashboard", "creator", "editor"]
        for ent in entities:
             if ent in msg_lower:
                  ctx.last_referenced_entity = ent
                  print(f"DEBUG: [TRACKER] Entity detected: {ent}")
                  if "panel" in ent or "logbook" in ent or "dashboard" in ent:
                       ctx.active_panel_id = ent
                  break

        if topic:
            ctx.last_topic = topic
            
        ctx.timestamp = datetime.now()
        logger.debug(f"[TRACKER] Updated context for {session_id}: {intent} | {topic} | Ref: {ctx.last_referenced_entity}")

    def set_mission(self, session_id: str, goal: str, swarm_id: Optional[str] = None):
        ctx = self.get_context(session_id)
        ctx.last_mission_goal = goal
        ctx.active_swarm_id = swarm_id
        ctx.last_topic = goal
        logger.info(f"[TRACKER] Context set to Mission: {goal}")

conversation_tracker = ConversationTracker()
