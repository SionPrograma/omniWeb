import logging
import uuid
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from ..intent_understanding.conversation_tracker import conversation_tracker, SessionContext

logger = logging.getLogger(__name__)

class MissionProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str
    action_type: str
    targets: List[str] = []
    payload: Dict[str, Any] = {}
    confidence: float = 1.0
    summary: str = ""

class DialogueActionBridge:
    """
    V1.0 Block 86: Dialogue-Led Mission Bridge.
    Translates clarified natural dialogue intent into structured Governed Proposals.
    """
    
    def propose_from_intent(self, session_id: str, intent: str, interpretation: Dict[str, Any]) -> Optional[MissionProposal]:
        """
        Analyzes current intent + context to see if we should stage a formal mission proposal.
        """
        ctx = conversation_tracker.get_context(session_id)
        
        # 1. ELIGIBILITY CHECK
        # Propose if: 
        # - Intent is heavy technical (Healing, Swap, Remediation)
        # - Conf is high
        # - Target entities are resolved
        
        target_intents = ["HEALING_INTENT", "STRATEGY_SWAP", "REMEDIATION_INTENT", "PROVIDER_UPDATE"]
        if intent not in target_intents and interpretation.get("intent") not in target_intents:
            return None

        # 2. RESOLVE TARGETS
        targets = ctx.active_entities if ctx.active_entities else []
        providers = ctx.active_providers if ctx.active_providers else []
        
        if not targets and not providers:
            # Ambiguous. Intent is clear but target is missing. 
            # We don't propose, we let the system ask "Which one?".
            return None

        # 3. BUILD PROPOSAL
        action_type = interpretation.get("intent") or intent
        goal = f"Acción gobernada: {action_type} sobre {', '.join(targets + providers)}"
        
        proposal = MissionProposal(
            goal=goal,
            action_type=action_type,
            targets=targets + providers,
            payload={
                "session_id": session_id,
                "triggered_by": "dialogue_bridge",
                "original_message": interpretation.get("refined_msg", ""),
                "entities": targets,
                "providers": providers
            },
            summary=f"Convertido de diálogo natural. Objetivo: {action_type}."
        )

        # 4. STAGE PROPOSAL (Cache in session metadata for 'Dale' resolution)
        ctx.metadata["pending_mission_proposal"] = proposal.model_dump()
        return proposal

    def resolve_confirmation(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Checks if the user is confirming a pending staged proposal.
        """
        ctx = conversation_tracker.get_context(session_id)
        pending = ctx.metadata.get("pending_mission_proposal") or ctx.metadata.get("last_suggested_action")
        
        if not pending:
            return None
            
        confirmation_keywords = ["dale", "ok", "adelante", "hacelo", "aplica", "si", "sí", "procede", "do it"]
        if any(w in message.lower() for w in confirmation_keywords):
            # Resolve!
            logger.info(f"[DIALOGUE_BRIDGE] Resolved confirmation for staged proposal in session {session_id}")
            # Clear it so it won't trigger again
            ctx.metadata["pending_mission_proposal"] = None
            return pending
            
        return None

dialogue_action_bridge = DialogueActionBridge()
