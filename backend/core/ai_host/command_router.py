from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
from .intent_classifier import intent_classifier
from .processors.base import AICommandResponse
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
from .processors.code_control_processor import CodeControlProcessor
from .processors.healing_processor import HealingProcessor
from .processors.status_processor import StatusProcessor
from .processors.generator_processor import GeneratorProcessor
from .processors.user_logbook_processor import UserLogbookProcessor
from .processors.user_graph_processor import UserGraphProcessor
from .processors.insight_processor import InsightProcessor
from .processors.permission_processor import PermissionProcessor

logger = logging.getLogger(__name__)


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
        self.registry.register("code_control", CodeControlProcessor())
        self.registry.register("healing", HealingProcessor())
        self.registry.register("status", StatusProcessor())
        self.registry.register("generator", GeneratorProcessor())
        self.registry.register("user_logbook", UserLogbookProcessor())
        self.registry.register("user_graph", UserGraphProcessor())
        self.registry.register("insight", InsightProcessor())
        self.registry.register("permission", PermissionProcessor())

        self.intents = {
            "open_chip": self._handle_open_chip,
            "log_entry": self._handle_log_entry,
            "show_system_status": self._handle_show_system_status,
            "show_logbook": self._handle_show_logbook,
            "launch_pipeline": self._handle_launch_pipeline,
            "create": self._handle_create,
            "activate": self._handle_activate,
            "deactivate": self._handle_deactivate,
            "list": self._handle_list,
            "workflow": self._handle_workflow,
            "insights": self._handle_insights,
            "suggest": self._handle_suggest,
            "modify": self._handle_modify,
            "memory": self._handle_memory,
            "graph": self._handle_graph,
            "antimodal": self._handle_antimodal,
            "knowledge": self._handle_knowledge,
            "healing": self._handle_healing
        }

    async def route(self, message: str, modality: str = "text", context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        from backend.core.permissions import set_chip_context
        user_id = context.get("user_id") if context else None
        
        with set_chip_context("core", user_id=user_id):
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
            
            # 1. Intent classification
            intent = intent_classifier.classify(msg)
            logger.info(f"CommandRouter: Detected intent '{intent}' for message: {msg}")

            # 2. Check registered processors for specialized handling (Phase 6/T)
            for proc in self.registry._processors.values():
                if await proc.can_handle(msg):
                    return await proc.process(msg, context=context)

            # 3. Route based on detected intent
            if intent and intent in self.intents:
                res = await self.intents[intent](msg)
                if res: return res

            # --- Legacy / Phase-specific Fallbacks ---

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

    async def _handle_open_chip(self, msg: str) -> AICommandResponse:
        from backend.core.module_registry import module_registry
        chips = module_registry.discover_all_chips()
        
        target = None
        # Remove verbs and common connector words
        noise = ["open", "abrir", "launch", "ejecutar", "lanzar", "chip", "entrar a", "go to", "the", "el", "la", "start", "inicia", "acceder", "run"]
        msg_clean = msg.lower()
        for word in noise:
            msg_clean = msg_clean.replace(word, "")
        msg_clean = msg_clean.strip()
        
        # Priority 1: Exact slug match
        for c in chips:
            if c["slug"].lower() == msg_clean:
                target = c["slug"]
                break
        
        # Priority 2: Keyword in message
        if not target:
            for c in chips:
                # Check for slug or name (partial match)
                if c["slug"].lower() in msg_clean or c["name"].lower() in msg_clean:
                    target = c["slug"]
                    break
                    
        # Priority 3: Fuzzy matching (fallback)
        if not target:
            for c in chips:
                if msg_clean in c["slug"].lower() or msg_clean in c["name"].lower():
                    target = c["slug"]
                    break
        
        if target:
            module_registry.log_execution(target)
            return AICommandResponse(
                intent="open_chip",
                status="success",
                message=f"I've located the '{target}' chip. Launching runtime environment now.",
                payload={"target": target, "action": "ACTIVATE_CHIP"}
            )
        
        available = ", ".join([c["slug"] for c in chips[:5]])
        return AICommandResponse(
            intent="open_chip", 
            status="error", 
            message=f"I couldn't find the chip you mentioned ('{msg_clean}'). Available chips include: {available}...",
            payload={"available_chips": [c["slug"] for c in chips]}
        )

    async def _handle_log_entry(self, msg: str) -> AICommandResponse:
        processor = self.registry.get_processor("logbook")
        return await processor.process(msg, "default_user")

    async def _handle_show_system_status(self, msg: str) -> AICommandResponse:
        processor = self.registry.get_processor("status")
        return await processor.process(msg)

    async def _handle_show_logbook(self, msg: str) -> AICommandResponse:
        processor = self.registry.get_processor("logbook")
        return await processor.process(msg, "default_user")

    async def _handle_launch_pipeline(self, msg: str) -> AICommandResponse:
        # Require confirmation for pipelines
        if "confirm" not in msg.lower() and "yes" not in msg.lower() and "si" not in msg.lower():
            return AICommandResponse(
                intent="confirmation_required",
                status="pending",
                message="⚠️ **Action Required**: Launching a pipeline consumes system credits and resources. Do you wish to proceed?",
                payload={"action": "launch_pipeline", "params": {"query": msg}}
            )

        # Implementation logic for pipeline simulation
        pipeline_name = "Translation Engine" if "translation" in msg.lower() else "Generic Flow"
        
        from backend.core.interface.visual_interface import visual_interface
        visual = visual_interface.create_visual_payload(
            "task-report",
            {
                "status": "running",
                "actions": [
                    "Initializing neural engine...",
                    "Loading language pairs...",
                    "Optimizing batch size",
                    "Security audit passed"
                ],
                "issues": []
            },
            f"Pipeline: {pipeline_name}"
        )

        return AICommandResponse(
            intent="launch_pipeline",
            status="success",
            message=f"✅ **{pipeline_name}** initialization sequence started. You can track progress in the background dashboard.",
            payload={
                "pipeline_name": pipeline_name,
                "pipeline_id": "gen-x-77", 
                "status": "running",
                "visual": visual
            }
        )

    async def _handle_create(self, msg: str) -> AICommandResponse:
        # Calls Chip Factory via Stability Loop
        from backend.core.chip_factory import chip_factory
        
        async def create_action():
            return await chip_factory.create_from_request(msg)
            
        loop_state, result = await loop_controller.execute_task(
            "create_chip",
            create_action,
            {"message": msg}
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

    async def _handle_healing(self, msg: str) -> AICommandResponse:
        """
        Delegates Healing/Self-Audit to specialized processor.
        """
        processor = self.registry.get_processor("healing")
        return await processor.process(msg)

ai_command_router = CommandRouter()
