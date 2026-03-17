import logging
import re
from typing import Optional, Dict, Any
from .intent_patterns import INTENT_GROUPS
from .semantic_context_builder import semantic_context_builder, SemanticContext
from .conversation_tracker import conversation_tracker

logger = logging.getLogger(__name__)

class IntentEngine:
    """
    Interprets user language semantically. 
    Handles incomplete prompts and context-based reconstruction.
    """
    
    async def understand(self, message: str, session_id: str) -> Dict[str, Any]:
        msg = message.lower().strip()
        logger.info(f"[INTENT_ENGINE] Processing: {msg}")
        
        # 1. BUILD SEMANTIC CONTEXT
        ctx = await semantic_context_builder.build(msg, session_id)
        
        # 2. DETECT CORE INTENT GROUP & SPECIFIC INTENT
        from ..routing.intent_classifier import intent_classifier
        specific_intent = intent_classifier.classify(msg)
        detected_group = self._detect_semantic_group(msg, ctx)
        
        # Mapping specific intents back to groups if needed
        if specific_intent == "healing":
            detected_group = "REMEDIATION_INTENT"
        elif specific_intent in ["creator_analysis", "creator_plan"]:
            detected_group = "ANALYSIS_INTENT" if specific_intent == "creator_analysis" else "BUILD_INTENT"

        # 3. RECONSTRUCT INCOMPLETE PROMPTS (Context-Awareness)
        if detected_group == "FOLLOW_UP_INTENT" and ctx.active_mission:
            logger.info(f"[INTENT_ENGINE] Reconstructed follow-up for mission: {ctx.active_mission}")
            if "build" in ctx.active_mission.lower() or "crea" in ctx.active_mission.lower():
                detected_group = "BUILD_INTENT"
            elif "arregla" in ctx.active_mission.lower() or "fix" in ctx.active_mission.lower():
                detected_group = "REMEDIATION_INTENT"

        # 4. DECIDE ROUTING MODE
        mode = self._decide_mode(detected_group, msg, ctx)
        
        # 5. UPDATE TRACKER
        conversation_tracker.update_context(session_id, message, detected_group)
        
        return {
            "intent_group": detected_group,
            "specific_intent": specific_intent,
            "mode": mode,
            "context": ctx
        }

    def _detect_semantic_group(self, msg: str, ctx: SemanticContext) -> str:
        # Simple fuzzy matching against our semantic groups
        for group, patterns in INTENT_GROUPS.items():
            if any(re.search(rf"\b{p}\b", msg) for p in patterns):
                return group
        
        # Contextual inference for very short messages
        if len(msg.split()) <= 2 and ctx.history.last_intent:
             # If it's short and we have a previous intent, it's likely a follow-up
             return "FOLLOW_UP_INTENT"
             
        return "CONVERSATIONAL_INTENT"

    def _decide_mode(self, group: str, msg: str, ctx: SemanticContext) -> str:
        """Translates semantic groups into Omni's execution modes."""
        words = len(msg.split())
        
        # IF input is command -> action_execution
        if group in ["BUILD_INTENT", "REMEDIATION_INTENT", "VOICE_COMMAND_INTENT"]:
            return "action_execution"
            
        # IF input is simple -> direct_response  
        if words <= 4 and group not in ["ANALYSIS_INTENT"]:
            return "direct_response"
            
        # ELSE -> reflective_analysis
        return "reflective_analysis"

intent_engine = IntentEngine()
