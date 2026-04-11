from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class SessionContext(BaseModel):
    """
    Volatile multi-turn context for a specific session.
    """
    intent_cluster: Optional[str] = None
    active_entities: List[str] = Field(default_factory=list)
    last_action_payload: Optional[Dict[str, Any]] = None
    pending_query_type: Optional[str] = None  # e.g., 'clarification', 'confirmation'
    last_hud_snapshot: Optional[Dict[str, Any]] = None
    turn_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
    confidence: float = 1.0

    def is_stale(self, seconds: int = 300) -> bool:
        return datetime.now() - self.last_updated > timedelta(seconds=seconds)

    def add_entity(self, entity: str):
        if entity and entity not in self.active_entities:
            self.active_entities.insert(0, entity)
            self.active_entities = self.active_entities[:5]  # Keep only recent 5

class ConversationalStateManager:
    """
    Manages conversational context across sessions.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConversationalStateManager, cls).__new__(cls)
            cls._instance.contexts: Dict[str, SessionContext] = {}
        return cls._instance

    def get_context(self, session_id: str) -> SessionContext:
        if session_id not in self.contexts or self.contexts[session_id].is_stale():
            self.contexts[session_id] = SessionContext()
        return self.contexts[session_id]

    def update_context(self, session_id: str, **kwargs):
        ctx = self.get_context(session_id)
        for key, value in kwargs.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)
        ctx.last_updated = datetime.now()
        ctx.turn_count += 1
        logger.debug(f"[CONV_STATE] Updated context for {session_id}: {kwargs}")

    def clear_context(self, session_id: str):
        if session_id in self.contexts:
            del self.contexts[session_id]
            logger.info(f"[CONV_STATE] Cleared context for {session_id}")

    def extract_entities(self, text: str) -> List[str]:
        """Simple rule-based entity extraction for providers/files."""
        entities = []
        # Common providers
        providers = ["openai", "deepseek", "anthropic", "aws", "elevenlabs", "local", "azure", "google"]
        for p in providers:
            if p in text.lower():
                entities.append(p)
        
        # Files (simple pattern)
        file_matches = [word for word in text.split() if "." in word and "/" in word]
        entities.extend(file_matches)
        
        return list(set(entities))

conversational_state = ConversationalStateManager()
