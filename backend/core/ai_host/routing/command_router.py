from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
from .intent_classifier import intent_classifier
from ..processors.base import AICommandResponse
from ..processors.knowledge_processor import KnowledgeProcessor
from ..processors.memory_processor import MemoryProcessor
from ..processors.graph_processor import GraphProcessor
from backend.core.stability_loop.loop_controller import loop_controller
from backend.core.stability_loop.loop_models import LoopStep
from backend.core.multimodal.multimodal_router import multimodal_router, MultimodalInput
from backend.core.multimodal.visual_response import VisualResponseEngine
from backend.core.antimodal.antimodal_controller import antimodal_controller
from backend.core.antimodal.antimodal_models import AntimodalMode
from ..processors.supercommand_processor import SuperCommandProcessor
from ..processors.logbook_processor import LogbookProcessor
from ..processors.code_control_processor import CodeControlProcessor
from ..processors.healing_processor import HealingProcessor
from ..processors.status_processor import StatusProcessor
from ..processors.generator_processor import GeneratorProcessor
from ..processors.user_logbook_processor import UserLogbookProcessor
from ..processors.user_graph_processor import UserGraphProcessor
from ..processors.insight_processor import InsightProcessor
from ..processors.permission_processor import PermissionProcessor
from ..processors.leadership_processor import LeadershipProcessor
from ..processors.guide_processor import GuideProcessor
from ..processors.governance_advisor_processor import GovernanceAdvisorProcessor
from ..processors.communication_processor import CommunicationProcessor
from ..processors.music_processor import MusicProcessor
from ..execution.executor import action_executor
from .utils import extract_chip_target, extract_idea_content, extract_memory_query
from ..memory.memory_router import memory_router

logger = logging.getLogger(__name__)


class CommandRouter:
    """
    Parses and routes natural language commands to system actions.
    """
    def __init__(self):
        from ..processors.registry import processor_registry
        self.registry = processor_registry
        
        # Import all processors
        from ..processors.creator_control_processor import CreatorControlProcessor
        from ..processors.general_chat_processor import GeneralChatProcessor
        from ..processors.diagnostic_processor import DiagnosticProcessor
        from ..processors.operational_processor import OperationalProcessor
        from ..processors.status_processor import StatusProcessor
        from ..processors.knowledge_processor import KnowledgeProcessor
        from ..processors.memory_processor import MemoryProcessor
        from ..processors.graph_processor import GraphProcessor
        from ..processors.supercommand_processor import SuperCommandProcessor
        from ..processors.logbook_processor import LogbookProcessor
        from ..processors.code_control_processor import CodeControlProcessor
        from ..processors.healing_processor import HealingProcessor
        from ..processors.generator_processor import GeneratorProcessor
        from ..processors.user_logbook_processor import UserLogbookProcessor
        from ..processors.user_graph_processor import UserGraphProcessor
        from ..processors.insight_processor import InsightProcessor
        from ..processors.permission_processor import PermissionProcessor
        from ..processors.leadership_processor import LeadershipProcessor
        from ..processors.guide_processor import GuideProcessor
        from ..processors.governance_advisor_processor import GovernanceAdvisorProcessor
        from ..processors.communication_processor import CommunicationProcessor
        from ..processors.music_processor import MusicProcessor

        # Register in priority order
        self.registry.register("operational", OperationalProcessor())
        self.registry.register("diagnostic", DiagnosticProcessor())
        self.registry.register("status", StatusProcessor())
        self.registry.register("chat", GeneralChatProcessor())
        self.registry.register("creator_control", CreatorControlProcessor())
        self.registry.register("knowledge", KnowledgeProcessor())
        self.registry.register("memory", MemoryProcessor())
        self.registry.register("graph", GraphProcessor())
        self.registry.register("supercommand", SuperCommandProcessor())
        self.registry.register("logbook", LogbookProcessor())
        self.registry.register("code_control", CodeControlProcessor())
        self.registry.register("healing", HealingProcessor())
        self.registry.register("generator", GeneratorProcessor())
        self.registry.register("user_logbook", UserLogbookProcessor())
        self.registry.register("user_graph", UserGraphProcessor())
        self.registry.register("insight", InsightProcessor())
        self.registry.register("permission", PermissionProcessor())
        self.registry.register("leadership", LeadershipProcessor())
        self.registry.register("guide", GuideProcessor())
        self.registry.register("governance_advisor", GovernanceAdvisorProcessor())
        self.registry.register("communication", CommunicationProcessor())
        self.registry.register("music", MusicProcessor())

        self.intents = {
            "open_chip": self._handle_open_chip,
            "inspect_chip": self._handle_open_chip,
            "navigate_to": self._handle_navigate_to,
            "focus_chip_runtime": self._handle_focus_chip_runtime,
            "list_chips": self._handle_list,
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
            "healing": self._handle_healing,
            "creator_command": self._handle_creator_command,
            "idea_captured": self._handle_memory_task,
            "list_ideas": self._handle_memory_task,
            "search_knowledge": self._handle_memory_task,
            "list_clusters": self._handle_memory_task,
            "show_cluster": self._handle_memory_task,
            "group_ideas": self._handle_memory_task,
            "summarize_cluster": self._handle_memory_task,
            "generate_project_draft": self._handle_memory_task,
            "initialize_project": self._handle_memory_task,
            "show_project_evolution": self._handle_memory_task,
            "show_cluster_lineage": self._handle_memory_task,
            "show_project_activity": self._handle_memory_task,
            "scan_projects": self._handle_memory_task,
            "generate_evolution_report": self._handle_memory_task,
            "get_project_timeline": self._handle_memory_task,
            "approve_roadmap": self._handle_builder_task,
            "start_execution": self._handle_builder_task,
            "acknowledgment": self._handle_acknowledgment,
            "creator_analysis": self._handle_brain_task,
            "creator_plan": self._handle_brain_task
        }

    async def route(self, message: str, modality: str = "text", context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        from backend.core.permissions import set_chip_context
        user_id = context.get("user_id") if context else "default_user"
        
        logger.info(f"[MESSAGE_RECEIVED] Modality: {modality} | Content: {message[:50]}...")

        try:
            with set_chip_context("core", user_id=user_id):
                # Multimodal Entrance
                input_v = MultimodalInput(modality=modality, raw_data=message)
                msg = await multimodal_router.handle_input(input_v)
                msg_clean = msg.lower().strip()

                # Creator Mode Prefix Detection
                creator_prefixes = ["omni", "creator", "system"]
                is_creator_prefixed = False
                for p in creator_prefixes:
                    if msg_clean.startswith(p):
                        is_creator_prefixed = True
                        if len(msg_clean) <= len(p) + 1:
                            msg_clean = p 
                        break

                logger.info(f"[ROUTER_FORWARD] Normalized Message: {msg_clean}")

                # Phase AA: Automatic Skill Discovery
                try:
                    import asyncio
                    from backend.core.skill_engine.skill_detector import skill_detector
                    asyncio.create_task(skill_detector.detect_from_input("default_user", msg_clean))
                except Exception as e:
                    logger.error(f"Skill Discovery Error: {e}")
                
                res = None
                
                # 1. SEMANTIC INTENT UNDERSTANDING
                from ..intent_understanding.intent_engine import intent_engine
                session_id = str(context.get("user_id", "default_user"))
                understanding = await intent_engine.understand(msg_clean, session_id)
                
                intent = understanding["specific_intent"]
                intent_group = understanding["intent_group"]
                semantic_ctx = understanding["context"]
                
                if is_creator_prefixed and (not intent or intent == "chat"):
                    intent = "creator_command"
                    
                logger.info(f"[INTENT_ENGINE_RESULT] Group: {intent_group} | Specific: {intent}")
                
                # --- PRIORITY CHAIN EXECUTION ---
                system_intents = ["list_chips", "show_logbook", "healing", "creator_command", "list"]
                chip_intents = ["open_chip", "inspect_chip", "activate", "deactivate"]
                nav_intents = ["navigate_to", "focus_chip_runtime"]
                memory_intents = ["idea_captured", "list_ideas", "search_knowledge", "list_clusters", "show_cluster", "group_ideas", "summarize_cluster", "generate_project_draft", "initialize_project", "show_project_evolution", "show_cluster_lineage", "show_project_activity", "scan_projects", "generate_evolution_report", "get_project_timeline"]
                brain_intents = ["creator_analysis", "creator_plan"]
                builder_intents = ["approve_roadmap", "start_execution"]
                
                priority_intents = system_intents + chip_intents + nav_intents + memory_intents + builder_intents + brain_intents
                
                if intent in priority_intents and intent in self.intents and intent not in brain_intents:
                    logger.info(f"[COMMAND_ROUTED] Priority Routing to intent handler: {intent}")
                    res = await self.intents[intent](msg_clean)

                # 3. UNIFIED COGNITIVE PIPELINE
                from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
                orchestrator = CognitiveOrchestrator(self)
                
                res = await orchestrator.orchestrate(
                    message=msg_clean, 
                    understanding=understanding,
                    context=context,
                    raw_response=res
                )
        except Exception as e:
            logger.error(f"[PIPELINE_ERROR] Route failed: {e}")
            from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
            orchestrator = CognitiveOrchestrator(self)
            
            error_res = AICommandResponse(
                intent="recovery", 
                status="success", 
                message="hmm… algo no terminó de tomar forma ahí" if "es" in message.lower() else "hmm… something didn't quite take shape there"
            )
            
            # FORCE orchestration even for errors
            res = await orchestrator.orchestrate(
                message=message,
                understanding={"mode": "direct_response", "intent_group": "RECOVERY"},
                context=context,
                raw_response=error_res
            )

        return await self._finalize_response(res, message)

    async def _finalize_response(self, res: AICommandResponse, original_msg: str) -> AICommandResponse:
        """Adds final touches to response logging."""
        # Antimodal adaptation and Telemetry are now handled by CognitiveOrchestrator
        # for a single unified pipeline.
        logger.info(f"[RESPONSE_READY] Intent: {res.intent} | Message: {res.message[:50]}...")
        return res

    async def _handle_open_chip(self, msg: str) -> AICommandResponse:
        from backend.core.module_registry import module_registry
        
        target = None
        # Robust chip extraction Step (Phase 0 Polish)
        msg_clean = extract_chip_target(msg)
        
        # Use centralized search
        chip_data = module_registry.search_chip(msg_clean)
        if chip_data:
            target = chip_data["slug"]
        
        if target:
            is_inspection = any(w in msg.lower() for w in ["inspect", "inspeccionar", "inspecciona", "inspeccioná", "ver", "audit", "audita"])
            intent = "inspect_chip" if is_inspection else "open_chip"
            
            # Execute through ActionExecutor
            execution = await action_executor.execute(intent, {"target": target})
            
            return AICommandResponse(
                intent=intent,
                status="success" if execution.get("success") else "error",
                message=execution.get("message", f"I've located the '{target}' chip. {'Preparing inspection report' if is_inspection else 'Launching runtime environment'} now."),
                payload={
                    "target": target, 
                    "action": execution.get("ui_instruction", {}).get("action", "ACTIVATE_CHIP"),
                    "execution": execution,
                    "ui_instruction": execution.get("ui_instruction")
                }
            )
        
        return AICommandResponse(
            intent="open_chip", 
            status="error", 
            message=f"I couldn't find the chip you mentioned ('{msg_clean}').",
            payload={}
        )

    async def _handle_navigate_to(self, msg: str) -> AICommandResponse:
        target = msg.replace("navigate to", "").replace("ir a", "").strip()
        execution = await action_executor.execute("navigate_to", {"target": target})
        return AICommandResponse(
            intent="navigate_to",
            status="success" if execution.get("success") else "error",
            message=f"Navegando a {target}..." if "es" in msg else f"Navigating to {target}...",
            payload={"execution": execution, "ui_instruction": execution.get("ui_instruction")}
        )

    async def _handle_focus_chip_runtime(self, msg: str) -> AICommandResponse:
        target = msg.replace("focus", "").replace("enfocar", "").strip()
        execution = await action_executor.execute("focus_chip_runtime", {"target": target})
        return AICommandResponse(
            intent="focus_chip_runtime",
            status="success" if execution.get("success") else "error",
            message=f"Enfocando chip {target}..." if "es" in msg else f"Focusing chip {target}...",
            payload={"execution": execution, "ui_instruction": execution.get("ui_instruction")}
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
        return AICommandResponse(intent="activate_chip", status="pending", message="Funcionalidad de activación en desarrollo.")

    async def _handle_deactivate(self, msg: str) -> AICommandResponse:
        return AICommandResponse(intent="deactivate_chip", status="pending", message="Funcionalidad de desactivación en desarrollo.")

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
        processor = self.registry.get_processor("memory")
        return await processor.process(msg)

    async def _handle_graph(self, msg: str) -> AICommandResponse:
        processor = self.registry.get_processor("graph")
        return await processor.process(msg)

    async def _handle_antimodal(self, msg: str) -> AICommandResponse:
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
        processor = self.registry.get_processor("knowledge")
        return await processor.process(msg)

    async def _handle_healing(self, msg: str) -> AICommandResponse:
        processor = self.registry.get_processor("healing")
        return await processor.process(msg)

    async def _handle_creator_command(self, msg: str) -> AICommandResponse:
        from ..brain_router import BrainRouter
        from backend.core.system_state.engine import state_engine
        from backend.core.omni_runtime.runtime_controller import runtime_controller
        
        brain = BrainRouter(self)
        system_state = await state_engine.get_state()
        
        brain_res = await brain.process(
            message=msg,
            runtime_context=runtime_controller.state,
            chip_registry=self.registry,
            system_state=system_state
        )
        if brain_res:
            return brain_res
            
        processor = self.registry.get_processor("creator_control")
        return await processor.process(msg)

    async def _handle_memory_task(self, msg: str) -> AICommandResponse:
        intent = intent_classifier.classify(msg) or "unknown"
        task_payload = msg
        if intent == "idea_captured":
            task_payload = extract_idea_content(msg)
        elif intent == "search_knowledge":
            task_payload = extract_memory_query(msg)
            
        return await memory_router.route_memory_task(intent, task_payload)

    async def _handle_builder_task(self, msg: str) -> AICommandResponse:
        from ..execution.builder_engine import builder_execution_engine
        from backend.core.master_logbook.models import EntryType
        from backend.core.master_logbook.manager import master_logbook_manager
        
        intent = intent_classifier.classify(msg)
        
        if intent == "approve_roadmap":
            # Find the latest roadmap
            entries = master_logbook_manager.get_entries(limit=10)
            roadmap = next((e for e in entries if e.type == EntryType.ROADMAP), None)
            
            if not roadmap:
                return AICommandResponse(intent=intent, status="error", message="No encontré ningún roadmap pendiente para aprobar.")
            
            task = await builder_execution_engine.initialize_from_roadmap(roadmap)
            return AICommandResponse(
                intent=intent,
                status="success",
                message=f"✅ Roadmap '{task.title}' aprobado. He inicializado el motor de ejecución. ¿Deseas comenzar la construcción ahora?",
                payload={"task_id": task.id, "roadmap_id": roadmap.id}
            )
            
        elif intent == "start_execution":
            # Find the latest pending task
            task = next(iter(builder_execution_engine.active_tasks.values()), None)
            # In a real scenario, we might look in the DB if not in memory
            
            if not task:
                return AICommandResponse(intent=intent, status="error", message="No hay ninguna tarea de construcción activa. Primero aprueba un roadmap.")
            
            await builder_execution_engine.start_execution(task.id)
            return AICommandResponse(
                intent=intent,
                status="success",
                message=f"🚀 Secuencia de ejecución iniciada para '{task.title}'. Podrás ver el progreso en la consola de construcción.",
                payload={"task_id": task.id}
            )
            
        return AICommandResponse(intent="builder_error", status="error", message="No pude procesar la tarea del constructor.")

    async def _handle_acknowledgment(self, msg: str) -> AICommandResponse:
        chat_proc = self.registry.get_processor("chat")
        return await chat_proc.process(msg)

    async def _handle_brain_task(self, msg: str) -> AICommandResponse:
        from ..brain_router import BrainRouter
        from backend.core.system_state.engine import state_engine
        from backend.core.omni_runtime.runtime_controller import runtime_controller
        
        brain = BrainRouter(self)
        system_state = await state_engine.get_state()
        
        return await brain.process(
            message=msg,
            runtime_context=runtime_controller.state,
            chip_registry=self.registry,
            system_state=system_state
        )

ai_command_router = CommandRouter()
