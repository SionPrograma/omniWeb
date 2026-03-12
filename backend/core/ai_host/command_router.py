from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
from .intent_classifier import intent_classifier
from .processors.knowledge_processor import KnowledgeProcessor
from .processors.memory_processor import MemoryProcessor
from .processors.graph_processor import GraphProcessor
from backend.core.stability_loop.loop_controller import loop_controller
from backend.core.stability_loop.loop_models import LoopStep
from backend.core.multimodal.multimodal_router import multimodal_router, MultimodalInput
from backend.core.multimodal.visual_response import VisualResponseEngine
from backend.core.antimodal.antimodal_controller import antimodal_controller
from backend.core.antimodal.antimodal_models import AntimodalMode
from .processors.supercommand_processor import SuperCommandProcessor
from .processors.logbook_processor import LogbookProcessor

logger = logging.getLogger(__name__)

class AICommandResponse(BaseModel):
    intent: str
    status: str
    message: str
    payload: Dict[str, Any] = {}

class CommandRouter:
    """
    Parses and routes natural language commands to system actions.
    """
    def __init__(self):
        # Processor Registry Integration (Phase T Readiness)
        from .processors.registry import processor_registry
        self.registry = processor_registry
        self.registry.register("knowledge", KnowledgeProcessor())
        self.registry.register("memory", MemoryProcessor())
        self.registry.register("graph", GraphProcessor())
        self.registry.register("supercommand", SuperCommandProcessor())
        self.registry.register("logbook", LogbookProcessor())

        self.intents = {
            "open": self._handle_open,
            "create": self._handle_create,
            "activate": self._handle_activate,
            "deactivate": self._handle_deactivate,
            "status": self._handle_status,
            "list": self._handle_list,
            "workflow": self._handle_workflow,
            "insights": self._handle_insights,
            "suggest": self._handle_suggest,
            "modify": self._handle_modify,
            "memory": self._handle_memory,
            "graph": self._handle_graph,
            "antimodal": self._handle_antimodal,
            "knowledge": self._handle_knowledge
        }

    async def route(self, message: str, modality: str = "text") -> AICommandResponse:
        # Multimodal Entrance
        input_v = MultimodalInput(modality=modality, raw_data=message)
        msg = await multimodal_router.handle_input(input_v)
        msg = msg.lower()

        # Phase AA: Automatic Skill Discovery
        try:
            from backend.core.skill_engine.skill_detector import skill_detector
            skill_detector.detect_from_input("default_user", msg)
        except Exception as e:
            logger.error(f"CommandRouter: Skill Discovery Error: {e}")
        
        res = None
        
        # 1. Master Logbook Detection (Should be one of the first things to check)
        logbook_keywords = ["log", "guarda", "anota", "registra", "idea", "bug", "fix", "tarea", "task", "decision"]
        is_logbook_intent = any(k in msg for k in logbook_keywords) and (
            "como" in msg or "esto" in msg or "sobre" in msg or "anota" in msg or "guarda" in msg or len(msg) > 15
        )
        
        log_res = None
        if is_logbook_intent:
            logger.info(f"CommandRouter: Logbook intent detected: {msg}")
            processor = self.registry.get_processor("logbook")
            log_res = await processor.process(msg, "default_user")
            # If the user explicitly asks to log/save/note, return immediately.
            early_return_keywords = ["log ", "guarda ", "anota ", "registra ", "save this", "note this"]
            if any(w in msg for w in early_return_keywords):
                return log_res

        # 2. Check for SuperCommand (Phase X)
        super_proc = self.registry.get_processor("supercommand")
        if super_proc and await super_proc.can_handle(msg):
            proc_res = await super_proc.process(msg)
            # Combine message if we logged something
            if log_res:
                proc_res.message = f"{log_res.message}\n\n{proc_res.message}"
            return proc_res

        # --- Other Domain Processors ---

        # 3. Education Engine Detection (Phase Z)
        education_keywords = ["enseñame", "aprender", "explicar", "clase", "curso", "leccion", "teach", "learn", "explain"]
        if any(k in msg for k in education_keywords):
            from backend.core.ai_host.processors.education_processor import education_processor
            topic = msg
            for k in education_keywords: topic = topic.replace(k, "")
            topic = topic.strip().strip(" sobre ").strip(" sobre el ").strip(" sobre la ")
            return await education_processor.process(topic, "default_user")

        # 4. Opportunity Engine Detection (Phase AA)
        opportunity_keywords = ["oportunidad", "empleo", "trabajo", "carrera", "opportunity", "job", "career"]
        if any(k in msg for k in opportunity_keywords):
            from backend.core.ai_host.processors.opportunity_processor import opportunity_processor
            return await opportunity_processor.process(msg, "default_user")

        # 5. Multi-AI Interface Detection (Phase AB)
        interface_keywords = ["abrir", "open", "invitar", "invite", "ventana", "window"]
        if any(k in msg for k in interface_keywords):
            from backend.core.ai_host.processors.interface_processor import interface_processor
            return await interface_processor.process(msg, "default_user")

        # 6. Spatial Interface Detection (Phase AC)
        spatial_keywords = ["proyectar", "project", "360", "espacio", "holograma", "hologram"]
        if any(k in msg for k in spatial_keywords):
            from backend.core.ai_host.processors.spatial_processor import spatial_processor
            return await spatial_processor.process(msg, "default_user")

        # 7. Swarm Engine Detection (Phase AD)
        swarm_keywords = ["enjambre", "swarm", "investiga", "research", "analiza", "multi"]
        if any(k in msg for k in swarm_keywords) and len(msg) > 15:
            from backend.core.ai_host.processors.swarm_processor import swarm_processor
            return await swarm_processor.process(msg, "default_user")

        # 8. Knowledge OS Detection (Phase AG - v2.0.0)
        os_keywords = ["sistema", "kernel", "modo", "os", "econom", "mercado", "evolucion"]
        if any(k in msg for k in os_keywords):
            from backend.core.ai_host.processors.os_processor import os_processor
            return await os_processor.process(msg, "default_user")

        # 9. Language Bridge Detection (Phase AH)
        bridge_keywords = ["traduccion", "bridge", "idioma", "traductor", "subtitulo", "habla"]
        if any(k in msg for k in bridge_keywords):
            from backend.core.ai_host.processors.bridge_processor import bridge_processor
            return await bridge_processor.process(msg, "default_user")

        # 10. Global Communication Detection (Phase AI)
        comm_keywords = ["llamada", "call", "sesion", "unirse", "comunicacion", "participantes"]
        if any(k in msg for k in comm_keywords):
            from backend.core.ai_host.processors.comm_processor import comm_processor
            return await comm_processor.process(msg, "default_user")

        # 11. Knowledge Domains Detection (Phase AJ)
        domain_keywords = ["dominio", "ciencia", "historia", "filosofia", "desarrollo humano"]
        if any(k in msg for k in domain_keywords):
            from backend.core.ai_host.processors.domain_processor import domain_processor
            return await domain_processor.process(msg, "default_user")

        # 12. Collaboration Spaces Detection (Phase AJ)
        collab_keywords = ["proyecto", "colaboracion", "investigacion", "nota", "espacio"]
        if any(k in msg for k in collab_keywords):
            from backend.core.ai_host.processors.collab_processor import collab_processor
            return await collab_processor.process(msg, "default_user")

        # 13. Existing intent classification
        intent = intent_classifier.classify(msg)
        
        if intent and intent in self.intents:
            res = await self.intents[intent](msg)
        elif not intent:
            # Fallback for knowledge as it has a broad semantic footprint
            if any(k in msg for k in ["explica", "explain", "que es", "what is"]):
                res = await self.intents["knowledge"](msg)
        
        if not res:
            # Fallback to Idea Cloud (Phase Y)
            from backend.core.idea_cloud.idea_capture import idea_capture
            idea = idea_capture.capture(msg)
            res = AICommandResponse(
                intent="idea_captured",
                status="success",
                message=f"He guardado tu pensamiento en la Nube de Ideas ('{msg[:30]}...'). Lo conectaré con tu conocimiento más tarde.",
                payload={"idea_id": idea.id, "topics": idea.topics}
            )

        # Antimodal adaptation (Phase 6)
        res.message = antimodal_controller.process_ai_response(res.message)

        # Telemetry (Phase F)
        try:
            from backend.core.usage.usage_tracker import usage_tracker
            usage_tracker.log_event(
                event_type="ai_command_executed",
                chip_slug="ai-host",
                metadata={
                    "intent": res.intent,
                    "status": res.status,
                    "message_preview": message[:50] # Privacy first
                }
            )
        except:
            pass

        return res

    async def _handle_open(self, msg: str) -> AICommandResponse:
        target = "none"
        if "finanzas" in msg or "finances" in msg: target = "finanzas"
        elif "reparto" in msg or "delivery" in msg: target = "reparto"
        elif "musica" in msg or "music" in msg: target = "musica"
        
        if target != "none":
            return AICommandResponse(
                intent="open_chip",
                status="success",
                message=f"Abriendo el chip {target}.",
                payload={"target": target, "action": "ACTIVATE_CHIP"}
            )
        return AICommandResponse(intent="open_chip", status="error", message="No encontré el chip a abrir.")

    async def _handle_create(self, msg: str) -> AICommandResponse:
        # Calls Chip Factory via Stability Loop
        from backend.core.chip_factory import chip_factory
        
        async def create_action():
            return await chip_factory.create_from_request(msg)
            
        loop_state, result = await loop_controller.execute_task(
            "create_chip",
            {"message": msg},
            create_action
        )
        
        if loop_state.current_step == LoopStep.COMPLETE and result["status"] == "success":
             return AICommandResponse(
                 intent="create_chip",
                 status="success",
                 message=f"{result['message']} [Estabilidad Verificada]",
                 payload={"chip": result["chip"], "loop_id": loop_state.task_id}
             )
        
        error_msg = result["detail"] if result and "detail" in result else "Error en la creación o inestabilidad detectada."
        return AICommandResponse(
            intent="create_chip", 
            status="error", 
            message=f"{error_msg} (Estado: {loop_state.current_step})",
            payload={"loop_id": loop_state.task_id}
        )

    async def _handle_activate(self, msg: str) -> AICommandResponse:
        # Implementation in Step 3
        return AICommandResponse(intent="activate_chip", status="pending", message="Funcionalidad de activación en desarrollo.")

    async def _handle_deactivate(self, msg: str) -> AICommandResponse:
        return AICommandResponse(intent="deactivate_chip", status="pending", message="Funcionalidad de desactivación en desarrollo.")

    async def _handle_status(self, msg: str) -> AICommandResponse:
        return AICommandResponse(intent="system_status", status="success", message="El sistema está operativo y saludable.", payload={})

    async def _handle_list(self, msg: str) -> AICommandResponse:
        from backend.core.module_registry import module_registry
        chips = module_registry.discover_all_chips()
        chip_names = [c["name"] for c in chips]
        return AICommandResponse(
            intent="list_chips",
            status="success",
            message=f"Chips instalados: {', '.join(chip_names)}",
            payload={"chips": chips}
        )

    async def _handle_workflow(self, msg: str) -> AICommandResponse:
        return AICommandResponse(intent="workflow_execute", status="pending", message="Motor de workflows en desarrollo.")

    async def _handle_insights(self, msg: str) -> AICommandResponse:
        from backend.core.self_improvement.proposal_engine import proposal_engine
        new_found = proposal_engine.generate_proposals()
        proposals = proposal_engine.get_pending_proposals()
        
        if not proposals:
            return AICommandResponse(
                intent="system_insights",
                status="success",
                message="No se detectaron nuevas áreas de mejora por ahora. ¡Tu sistema está optimizado!",
                payload={}
            )
        
        desc = "He detectado algunas oportunidades de optimización:\n" + "\n".join([f"- {p['description']}" for p in proposals])
        return AICommandResponse(
            intent="system_insights",
            status="success",
            message=desc,
            payload={"proposals": proposals}
        )

    async def _handle_suggest(self, msg: str) -> AICommandResponse:
        from backend.core.user_context.context_model import context_model
        from backend.core.user_context.habit_detector import habit_detector
        from backend.core.user_context.routine_analyzer import routine_analyzer
        
        # Analyze current context
        habit_detector.detect_habits()
        routine_analyzer.detect_routines()
        
        patterns = context_model.get_patterns()
        if not patterns:
            return AICommandResponse(
                intent="suggest_context",
                status="success",
                message="Aún estoy aprendiendo tus hábitos. Por ahora, ¿cómo puedo ayudarte?",
                payload={}
            )
            
        # Select best suggestion based on time (routine)
        import datetime
        hour = datetime.datetime.now().hour
        suggested_chips = []
        
        for p in patterns:
            if p["type"] == "routine":
                if p["data"]["routine_type"] == "morning" and 6 <= hour < 12:
                    suggested_chips.append(p["data"]["chip"])
                elif p["data"]["routine_type"] == "evening" and 18 <= hour < 24:
                    suggested_chips.append(p["data"]["chip"])
                    
        if suggested_chips:
            chips_str = ", ".join(list(set(suggested_chips)))
            return AICommandResponse(
                intent="suggest_context",
                status="success",
                message=f"Basado en tu rutina, ¿quieres que prepare el entorno con: {chips_str}?",
                payload={"suggested_chips": suggested_chips, "action": "PREPARE_ROUTINE"}
            )
            
        return AICommandResponse(
            intent="suggest_context",
            status="success",
            message="No encontré una rutina específica para este momento, pero puedo abrir tus favoritos si lo deseas.",
            payload={}
        )

    async def _handle_modify(self, msg: str) -> AICommandResponse:
        from backend.core.ai_developer.code_analyzer import code_analyzer
        from backend.core.ai_developer.patch_generator import patch_generator
        from backend.core.ai_developer.chip_editor import chip_editor
        from backend.core.ai_developer.module_reloader import module_reloader
        
        # Determine target chip
        from backend.core.module_registry import module_registry
        chips = module_registry.discover_all_chips()
        target = None
        for c in chips:
            if c["slug"] in msg:
                target = c["slug"]
                break
        
        if not target:
            return AICommandResponse(intent="modify_chip", status="error", message="Debes especificar un chip válido para modificar.")
            
        async def modify_action():
            # 1. Analyze
            analysis = code_analyzer.analyze_chip(target)
            # 2. Generate Patch
            patches = patch_generator.generate_patch(msg, analysis)
            if not patches:
                 raise Exception("No se pudieron generar parches.")
            # 3. Apply
            result = chip_editor.apply_patches(target, patches)
            if result["status"] == "error":
                 raise Exception(result["message"])
            # 4. Reload
            module_reloader.reload_chip(target)
            return result

        loop_state, result = await loop_controller.execute_task(
            "modify_chip",
            modify_action,
            {"chip_slug": target, "message": msg}
        )
        
        if loop_state.current_step == LoopStep.COMPLETE:
            from backend.core.interface.visual_interface import visual_interface
            visual = visual_interface.create_visual_payload(
                "chip-modification-success",
                f"Modificado {len(result['applied'])} archivos en {target}",
                f"AI Developer: {target} (Estable)"
            )

            return AICommandResponse(
                intent="modify_chip",
                status="success",
                message=f"El chip '{target}' ha sido modificado, recargado y su estabilidad verificada.",
                payload={
                    "applied": result["applied"], 
                    "backup": result["backup"],
                    "visual": visual,
                    "loop_id": loop_state.task_id
                }
            )
        
        return AICommandResponse(
            intent="modify_chip", 
            status="error", 
            message=f"No se pudo estabilizar el chip '{target}' tras la modificación.",
            payload={"loop_id": loop_state.task_id}
        )
    
    async def _handle_memory(self, msg: str) -> AICommandResponse:
        """
        Delegates Memory Dialogue Mode to specialized processor.
        """
        processor = self.registry.get_processor("memory")
        return await processor.process(msg)

    async def _handle_graph(self, msg: str) -> AICommandResponse:
        """
        Delegates Knowledge Graph Mode to specialized processor.
        """
        processor = self.registry.get_processor("graph")
        return await processor.process(msg)

    async def _handle_antimodal(self, msg: str) -> AICommandResponse:
        """
        Handles Antimodal command routing.
        Examples: "activa modo silencioso", "ponete en modo compacto", "solo dame resúmenes"
        """
        mode = AntimodalMode.STANDARD
        action = "ENABLE"
        
        if "desactiva" in msg or "disable" in msg or "estándar" in msg or "standard" in msg:
            mode = AntimodalMode.STANDARD
            action = "DISABLE"
        elif "silencio" in msg or "silent" in msg:
            mode = AntimodalMode.SILENT
        elif "compact" in msg or "compacto" in msg:
            mode = AntimodalMode.COMPACT
        elif "fondo" in msg or "background" in msg:
            mode = AntimodalMode.BACKGROUND
        elif "distraccion" in msg or "distraction" in msg or "foco" in msg or "focus" in msg:
            mode = AntimodalMode.LOW_DISTRACTION
        elif "resumen" in msg or "summary" in msg or "solo dame" in msg:
            mode = AntimodalMode.SUMMARY_ONLY
            
        antimodal_controller.set_mode(mode)
        
        status_msg = f"Modo antimodal '{mode.value}' activado."
        if action == "DISABLE":
            status_msg = "Modo antimodal desactivado. Volviendo a interfaz estándar."
            
        return AICommandResponse(
            intent="antimodal_mode_change",
            status="success",
            message=status_msg,
            payload={"mode": mode.value, "status": antimodal_controller.get_status_summary()}
        )

    async def _handle_knowledge(self, msg: str) -> AICommandResponse:
        """
        Delegates Knowledge Dialogue Mode to specialized processor.
        """
        processor = self.registry.get_processor("knowledge")
        return await processor.process(msg)

ai_command_router = CommandRouter()
