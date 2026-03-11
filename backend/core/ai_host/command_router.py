from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
from backend.core.stability_loop.loop_controller import loop_controller
from backend.core.stability_loop.loop_models import LoopStep
from backend.core.multimodal.multimodal_router import multimodal_router, MultimodalInput
from backend.core.multimodal.visual_response import VisualResponseEngine
from backend.core.antimodal.antimodal_controller import antimodal_controller
from backend.core.antimodal.antimodal_models import AntimodalMode

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
            "antimodal": self._handle_antimodal
        }

    async def route(self, message: str, modality: str = "text") -> AICommandResponse:
        # Multimodal Entrance
        input_v = MultimodalInput(modality=modality, raw_data=message)
        msg = await multimodal_router.handle_input(input_v)
        msg = msg.lower()
        
        res = None
        
        # Simple rule-based intent classification
        if "abrir" in msg or "open" in msg:
             res = await self.intents["open"](msg)
        elif "crea" in msg or "create" in msg:
             res = await self.intents["create"](msg)
        elif "activa" in msg or "activate" in msg:
             res = await self.intents["activate"](msg)
        elif "desactiva" in msg or "deactivate" in msg:
             res = await self.intents["deactivate"](msg)
        elif "estado" in msg or "status" in msg or "salud" in msg:
             res = await self.intents["status"](msg)
        elif "listar" in msg or "list" in msg or "chips" in msg:
             res = await self.intents["list"](msg)
        elif "preparar" in msg or "sugiere" in msg or "sesión" in msg:
             res = await self.intents["suggest"](msg)
        elif "insight" in msg or "mejorar" in msg or "optimizar" in msg or "sugerencia" in msg or "mejora" in msg:
             res = await self.intents["insights"](msg)
        elif "workflow" in msg or "flujo" in msg:
             res = await self.intents["workflow"](msg)
        elif "modificar" in msg or "modify" in msg or "parche" in msg:
             res = await self.intents["modify"](msg)
        elif "recordar" in msg or "memory" in msg or "historia" in msg or "continuar" in msg or "resume" in msg or "recall" in msg:
             res = await self.intents["memory"](msg)
        elif "explora" in msg or "explore" in msg or "relacion" in msg or "relates" in msg or "camino" in msg or "path" in msg or "grafo" in msg or "graph" in msg:
             res = await self.intents["graph"](msg)
        elif "antimodal" in msg or "silencio" in msg or "silent" in msg or "compact" in msg or "fondo" in msg or "background" in msg or "distraccion" in msg or "distraction" in msg or "resumen" in msg or "summary" in msg:
             res = await self.intents["antimodal"](msg)
        
        if not res:
            res = AICommandResponse(
                intent="unknown",
                status="error",
                message="Lo siento, no entiendo ese comando.",
                payload={}
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
            {"chip_slug": target, "message": msg},
            modify_action
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
        from backend.core.long_memory.memory_retriever import memory_retriever
        
        # 1. Handle "continue/resume project"
        if "continuar" in msg or "resume" in msg or "proyecto" in msg:
            projects = memory_retriever.get_recent_projects()
            if projects:
                p = projects[0]
                return AICommandResponse(
                    intent="memory_recall",
                    status="success",
                    message=f"Hablemos de tu último proyecto: '{p.title}'. ¿Quieres continuar donde lo dejaste?",
                    payload={"memory": p}
                )
            return AICommandResponse(intent="memory_recall", status="error", message="No encontré proyectos recientes para continuar.")

        # 2. General recall
        memories = memory_retriever.find_relevant_memories(msg)
        if memories:
            m = memories[0]
            desc = f"He recordado esto: {m.summary}"
            return AICommandResponse(
                intent="memory_recall",
                status="success",
                message=desc,
                payload={"memories": memories}
            )
            
        return AICommandResponse(intent="memory_recall", status="error", message="No tengo recuerdos claros sobre eso aún.")

    async def _handle_graph(self, msg: str) -> AICommandResponse:
        from backend.core.knowledge_graph.graph_query import GraphQueryEngine
        from backend.core.knowledge_graph.graph_builder import GraphBuilder
        
        query_engine = GraphQueryEngine()
        builder = GraphBuilder()
        
        # Proactively build/update graph from memory if requested or if we are exploring
        if "sincronizar" in msg or "sync" in msg or "build" in msg:
            builder.process_all_memories()
            return AICommandResponse(
                intent="graph_sync",
                status="success",
                message="Grafo de conocimiento sincronizado con la memoria a largo plazo.",
                payload={}
            )

        # 1. Related Topics / Explore
        if "explora" in msg or "explore" in msg or "relacion" in msg or "relates" in msg:
            # Extract topic - simple word after explore/explora
            parts = msg.replace("explora", "").replace("explore", "").replace("relacionado con", "").replace("relates to", "").split()
            if parts:
                topic = parts[0].strip(",.?!")
                related = query_engine.get_related_topics(topic)
                if related:
                    topics_str = ", ".join([f"{r['name']} ({r['relationship']})" for r in related])
                    
                    # Add Visual Graph Payload
                    visual = VisualResponseEngine.create_table(
                        f"Relaciones de {topic}",
                        ["Destino", "Tipo", "Relación"],
                        [[r["name"], r["type"], r["relationship"]] for r in related]
                    )
                    
                    return AICommandResponse(
                        intent="graph_explore",
                        status="success",
                        message=f"Explorando '{topic}'. Temas relacionados: {topics_str}.",
                        payload={"root": topic, "related": related, "visual": visual}
                    )
                return AICommandResponse(intent="graph_explore", status="error", message=f"No encontré conexiones for '{topic}'. Prueba sincronizar el grafo.")

        # 2. Learning Path
        if "camino" in msg or "path" in msg or "aprender" in msg or "learn" in msg:
             parts = msg.split()
             topic = parts[-1].strip(",.?!")
             path = query_engine.suggest_learning_path(topic)
             if path:
                 path_str = " -> ".join([p["name"] for p in path])
                 return AICommandResponse(
                     intent="graph_learning_path",
                     status="success",
                     message=f"Camino de aprendizaje para {topic}: {path_str}",
                     payload={"path": path}
                 )
        
        # 3. Project Graph
        if "grafo" in msg or "graph" in msg or "proyecto" in msg:
             # Default to general graph info if no specific project
             nodes = query_engine.store.get_all_nodes()
             return AICommandResponse(
                 intent="graph_view",
                 status="success",
                 message=f"El grafo de conocimiento actual contiene {len(nodes)} conceptos interconectados.",
                 payload={"nodes_count": len(nodes)}
             )

        return AICommandResponse(intent="graph_query", status="error", message="No pude procesar tu consulta del grafo.")

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

ai_command_router = CommandRouter()
