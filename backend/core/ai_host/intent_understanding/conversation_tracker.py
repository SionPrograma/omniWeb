import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SessionContext(BaseModel):
    last_topic: Optional[str] = None
    last_intent: Optional[str] = None
    last_mission_goal: Optional[str] = None
    last_referenced_entity: Optional[str] = None # For 'eso', 'este'
    last_suggested_action: Optional[Dict[str, Any]] = None # For 'dale', 'hacelo'
    active_providers: List[str] = [] # Tracked providers (openai, deepseek, etc.)
    active_panel_id: Optional[str] = None # For 'ese panel', 'acá'
    active_swarm_id: Optional[str] = None
    history: List[Dict[str, str]] = [] # [{"role": "user", "content": "..."}, {"role": "omni", "content": "..."}]
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence_score: float = 1.0 # Strength of current conversational thread

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
                        ctx.history.append({"role": "user", "content": item['prompt']})
                    if 'response' in item:
                        ctx.history.append({"role": "omni", "content": item['response']})
                
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
        
        # Check staleness (5 minute TTL for active strategic context)
        ctx = self.sessions[session_id]
        if (datetime.now() - ctx.timestamp).total_seconds() > 300:
             logger.info(f"[TRACKER] Context for {session_id} stale. Refreshing.")
             # Preserve last 5 history turns for continuity but reset trackers
             self.sessions[session_id] = SessionContext(history=ctx.history[-5:])
             
        return self.sessions[session_id]

    def update_context(self, session_id: str, message: str, intent: str, topic: Optional[str] = None, role: str = "user", payload: Optional[Dict[str, Any]] = None):
        print(f"DEBUG: [TRACKER] update_context called for {session_id} with {role} msg: '{message[:30]}...'")
        ctx = self.get_context(session_id)
        
        if role == "user":
            ctx.last_intent = intent
            
        ctx.history.append({"role": role, "content": message})
        if len(ctx.history) > 20: # Keep up to 10 turns (20 msgs)
            ctx.history.pop(0)
        
        if role == "user":
            # ENTITY SCANNING (Identify what the user is talking about right now)
            msg_lower = message.lower()
            
            # Expanded entities for Block 84 (Forge Providers + Core Components)
            entities = ["openai", "deepseek", "anthropic", "aws", "elevenlabs", "local", "azure", "google", "lingua", "forge", "ledger", "logbook", "dashboard", "editor"]
            
            detected_providers = []
            for ent in entities:
                 if ent in msg_lower:
                      ctx.last_referenced_entity = ent
                      # Collect providers separately
                      if ent in ["openai", "deepseek", "anthropic", "aws", "elevenlabs", "local", "azure", "google"]:
                           detected_providers.append(ent)
                      
                      if "panel" in ent or "logbook" in ent or "dashboard" in ent:
                           ctx.active_panel_id = ent
            
            if detected_providers:
                 ctx.active_providers = detected_providers
                 print(f"DEBUG: [TRACKER] Providers detected in context: {detected_providers}")

        if payload:
             ctx.last_suggested_action = payload
             print(f"DEBUG: [TRACKER] Suggested action payload cached in context.")

        if topic and intent not in ["NATURAL_CHAT", "GREETING", "acknowledgment", "identity", "how_are_you", "greeting", "smalltalk"]:
            ctx.last_topic = topic
            
        ctx.timestamp = datetime.now()
        logger.debug(f"[TRACKER] Updated context for {session_id}: {intent} | {ctx.last_topic} | Ref: {ctx.last_referenced_entity}")

    def set_mission(self, session_id: str, goal: str, swarm_id: Optional[str] = None):
        ctx = self.get_context(session_id)
        ctx.last_mission_goal = goal
        ctx.active_swarm_id = swarm_id
        ctx.last_topic = goal
        logger.info(f"[TRACKER] Context set to Mission: {goal}")

conversation_tracker = ConversationTracker()
