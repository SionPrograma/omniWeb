import logging
from typing import Dict, Any, Optional
from backend.core.ai_host.processors.base import AICommandResponse
from backend.core.system_state.engine import state_engine
from backend.core.omni_runtime.runtime_controller import runtime_controller
from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.memory.semantic_memory import semantic_memory

logger = logging.getLogger(__name__)

class CognitiveOrchestrator:
    """
    Cognitive Orchestration Layer (Additive / Non-Destructive)
    Connects:
    1. Deliberation Layer (BrainRouter)
    2. System State & Chips Awareness
    3. Memory & Logbook Context
    4. Response Normalization (Natural Language)
    """
    
    def __init__(self, command_router):
        self.command_router = command_router
        self.brain = BrainRouter(self.command_router)
        
    async def orchestrate(
        self, 
        message: str, 
        understanding: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> AICommandResponse:
        
        session_id = str(context.get("user_id", "default_user")) if context else "default_user"
        
        logger.info(f"[ORCHESTRATOR] Received Intent: {understanding.get('intent_group', 'unknown')} | Mode: {understanding.get('mode', 'conversational')}")

        # 1. State & Chip Awareness Integration
        system_state = await state_engine.get_state()
        runtime_ctx = runtime_controller.state
        
        # 2. Context Integration (Recent conversation via semantic memory)
        recent_context = []
        try:
            recent_interactions = semantic_memory.get_recent_interactions(session_id, limit=3)
            recent_context = [f"User: {m.get('prompt', '')} | Omni: {m.get('response', '')}" for m in recent_interactions]
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Memory integration warning: {e}")
            
        enhanced_understanding = dict(understanding)
        enhanced_understanding["recent_conversation"] = recent_context
        
        # 3. Deliberation Output (Connect to Brain)
        try:
            brain_response = await self.brain.process(
                message=message,
                context=context,
                runtime_context=runtime_ctx,
                chip_registry=self.command_router.registry,
                system_state=system_state,
                understanding=enhanced_understanding
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Brain Deliberation Failed: {e}")
            brain_response = None
            
        # 3.1 Messaging Priority Fallback
        if not brain_response or brain_response.intent == "chat":
            comm_proc = self.command_router.registry.get_processor("communication")
            if comm_proc and await comm_proc.can_handle(message):
                try:
                    res = await comm_proc.process(message, context=context)
                    if res: brain_response = res
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Messaging processor error: {e}")

        # 3.2 Other Processors Fallback
        if not brain_response or brain_response.intent == "chat":
            for name, proc in self.command_router.registry._processors.items():
                if name in ["communication", "chat"]: continue 
                try:
                    if await proc.can_handle(message):
                        res = await proc.process(message, context=context)
                        if res: 
                            brain_response = res
                            break
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Processor '{name}' error: {e}")

        # 4. Fallback Prevention
        if not brain_response:
            logger.info("[ORCHESTRATOR] Processors bypassed, using Cognitive-Aware Conversational Fallback.")
            chat_proc = self.command_router.registry.get_processor("chat")
            if chat_proc:
                brain_response = await chat_proc.process(message, context=context)
                if not brain_response:
                    brain_response = AICommandResponse(
                        intent="orchestrator_fallback", 
                        status="success", 
                        message=f"Estoy analizando tu solicitud. Mis subsistemas reportan estado {system_state.health.value}. ¿Te refieres a un módulo particular de OmniWeb?"
                    )
            else:
                brain_response = AICommandResponse(
                    intent="orchestrator_fallback", 
                    status="success", 
                    message=f"Proceso orquestado finalizado. Estado del sistema: {system_state.health.value}. ¿Reintentamos la orden?"
                )

        # 5. Normalization (Natural Language & Unified tone)
        brain_response.message = self._normalize_response(brain_response.message, system_state)
        
        return brain_response

    def _normalize_response(self, text: str, system_state: Any) -> str:
        """
        Ensures response coherence without breaking structured outputs like logs or plans.
        Only adjusts plain conversational text to be more organically aware.
        """
        if not text:
            return "El proceso ha sido completado y reportado a logbook."
            
        # Exclude normalization if the text contains markdown tables, lists, or clear structures
        if "**" in text or "```" in text or "OBSERVATION" in text or "OBSERVACIÓN" in text or "- " in text or "CONFIDENCE" in text:
            return text
            
        # Adjust very generic responses to feel grounded
        generic_replies = ["Entendido.", "Okay.", "Comprendido.", "Got it.", "Alright.", "Perfecto.", "Bien.", "Vale."]
        stripped_text = text.strip()
        is_generic = stripped_text in generic_replies or stripped_text in [g.lower() for g in generic_replies]
        
        # Check if they are short sentences that feel robotic
        if is_generic or len(stripped_text.split()) < 4:
            health = system_state.health.value
            if health == "healthy":
                return f"{text} Los sistemas base operan correctamente. ¿Qué te gustaría hacer ahora?"
            elif health == "warning":
                return f"{text} (Por cierto, detecto advertencias no críticas en {health.upper()}). Sigo escuchando."
            else:
                return f"{text} (Estado del sistema: {health.upper()}). ¿Algún comando adicional?"
            
        return text

orchestrator = None # Will be initialized by CommandRouter
