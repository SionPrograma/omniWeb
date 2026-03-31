import logging
import re
from typing import Optional, Dict, Any
from .intent_patterns import INTENT_GROUPS
from .semantic_context_builder import semantic_context_builder, SemanticContext
from .human_input_interpreter import human_interpreter
from .conversation_tracker import conversation_tracker

logger = logging.getLogger(__name__)

class IntentEngine:
    """
    Interprets user language semantically. 
    Handles incomplete prompts and context-based reconstruction.
    """
    
    async def understand(self, message: str, session_id: str) -> Dict[str, Any]:
        msg = message.lower().strip()
        logger.info(f"[INTENT_ENGINE] Raw input received: {msg}")
        
        # 1. HUMAN INPUT INTERPRETATION (Preprocessing messy input)
        interpretation = human_interpreter.interpret(msg)
        clarity = interpretation.get("clarity")
        
        # 2. BUILD SEMANTIC CONTEXT (Enhanced with interpretation)
        refined_msg = interpretation.get("refined_text", msg)
        ctx = await semantic_context_builder.build(refined_msg, session_id)
        ctx.interpretation = interpretation # Attach interpretation to context
        
        # 2.5 SEMANTIC RECONSTRUCTION (Surgical context injection)
        if clarity == "follow_up":
            from ..memory.mission_manager import mission_manager
            active_mission = mission_manager.get_active_mission()
            if active_mission:
                refined_msg = f"Continúa con la misión: {active_mission.active_goal}. Acción específica: {refined_msg}"
                print(f"DEBUG: [RECONSTRUCTION] Follow-up mapped to Mission: {active_mission.active_goal}")
            elif ctx.history.last_topic:
                refined_msg = f"Continúa hablando de/haciendo: {ctx.history.last_topic}. Acción específica: {refined_msg}"
                print(f"DEBUG: [RECONSTRUCTION] Follow-up mapped to Topic: {ctx.history.last_topic}")

        elif clarity == "vague":
            if ctx.history.last_referenced_entity:
                refined_msg = refined_msg.replace("eso", ctx.history.last_referenced_entity)
                refined_msg = refined_msg.replace("ese", ctx.history.last_referenced_entity)
                refined_msg = f"{refined_msg} (Referencia: {ctx.history.last_referenced_entity})"
                print(f"DEBUG: [RECONSTRUCTION] Vague resolved to: {ctx.history.last_referenced_entity}")
            elif ctx.history.active_panel_id:
                panel_name = ctx.history.active_panel_id.replace("-", " ")
                refined_msg = f"{refined_msg} (En el panel: {panel_name})"
                print(f"DEBUG: [RECONSTRUCTION] Spatial resolved to: {panel_name}")

        # 3. DETECT CORE INTENT GROUP & SPECIFIC INTENT
        from ..routing.intent_classifier import intent_classifier
        specific_intent = intent_classifier.classify(refined_msg)
        detected_group = self._detect_semantic_group(refined_msg, ctx)
        
        # Mapping specific intents back to groups if needed
        if specific_intent == "healing":
            detected_group = "REMEDIATION_INTENT"
        elif specific_intent in ["creator_analysis", "creator_plan"]:
            detected_group = "ANALYSIS_INTENT" if specific_intent == "creator_analysis" else "BUILD_INTENT"
        elif specific_intent == "system_audit" and detected_group != "OPERATIONAL_DIAGNOSTIC":
            # Only use system_audit group if we didn't already detect a concrete operational failure
            detected_group = "SYSTEM_AUDIT_INTENT"
        elif specific_intent == "copilot_proposal":
            detected_group = "COPILOT_PROPOSAL_INTENT"
        elif detected_group == "OPERATIONAL_DIAGNOSTIC":
            specific_intent = "operational_failure_report"
        elif specific_intent in ["memory_continuity", "memory_project"] and detected_group not in ["OPERATIONAL_DIAGNOSTIC", "REMEDIATION_INTENT"]:
            detected_group = "MEMORY_INTENT"

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
            "context": ctx,
            "refined_message": refined_msg
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
             
        # Default now fallback to NATURAL_CHAT for better balance
        return "NATURAL_CHAT"

    def _decide_mode(self, group: str, msg: str, ctx: SemanticContext) -> str:
        """Translates semantic groups into Omni's execution modes."""
        words = len(msg.split())
        msg_lower = msg.lower()
        
        # 1. PRIORITY MODE: Operational Diagnostic (Must take precedence over format signals)
        if group == "OPERATIONAL_DIAGNOSTIC":
            return "operational_diagnostic"

        # 2. DETECT CONSTRAINED OUTPUT SIGNAL (SOLO, ONLY, FORMATO, EXACTO)
        constrained_signals = [
            r"\bsolo\b", r"\bonly\b", r"\bformato\b", r"\bexacto\b", r"\bexacta\b", 
            r"archivo_leido", r"primera_linea", 
            r"microfix_propuesto", r"impacto_relacionado"
        ]
        if any(re.search(s, msg_lower) for s in constrained_signals):
            return "constrained_output"
        
        # 3. IF input is command -> action_execution
        if group in ["BUILD_INTENT", "REMEDIATION_INTENT", "VOICE_COMMAND_INTENT", "EXPLORATION_INTENT", "SYSTEM_AUDIT_INTENT"]:
            return "action_execution"
            
        if group == "SYSTEM_AUDIT_INTENT":
            return "reflective_analysis"
            
        # 4. IF input is clearly conversational -> natural_chat
        if group == "NATURAL_CHAT":
            return "natural_chat"

        # 5. IF input is simple or synthesis/memory request -> direct_response  
        # This covers both short messages and synthesis/memory requests regardless of length
        if group in ["COGNITIVE_SYNTHESIS", "MEMORY_INTENT"] or (words <= 4 and group not in ["ANALYSIS_INTENT", "OPERATIONAL_DIAGNOSTIC"]):
            # For memory intent, check if it's conversational
            if group == "MEMORY_INTENT":
                conv_keywords = ["che", "andabamos", "andábamos", "haciendo", "que tal", "qué tal", "omni", "andabas", "hicimos"]
                if any(k in msg_lower for k in conv_keywords):
                    return "natural_chat"
            return "direct_response"
            
        # 6. ELSE -> reflective_analysis
        return "reflective_analysis"

intent_engine = IntentEngine()
