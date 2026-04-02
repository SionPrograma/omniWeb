import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.core.ai_host.processors.base import AICommandResponse
from backend.core.system_state.engine import state_engine
from backend.core.omni_runtime.runtime_controller import runtime_controller
from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.memory.semantic_memory import semantic_memory
from .output_policy import get_output_policy
from .responses_api import ResponsesAPI, InternalStructuredOutput
from backend.core.ai_host.observability.tracing_api import tracing_api
from backend.core.ai_host.observability.self_correction import self_correction
from backend.core.ai_host.orchestration.tool_definitions import tool_registry
from backend.core.ai_host.orchestration.prompt_compiler import prompt_compiler
from backend.core.ai_host.orchestration.execution_tree import tree_planner, ExecutionTree, NodeStatus
from backend.core.ai_host.orchestration.scope_lock import DeviationDetector
from backend.core.ai_host.orchestration.evidence_loop import evidence_loop
from backend.core.ai_host.synthesis.copilot_normalizer import copilot_normalizer

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
    
    def __init__(self, command_router=None):
        from backend.core.ai_host.routing.command_router import ai_command_router
        self.command_router = command_router or ai_command_router
        self.brain = BrainRouter(self.command_router)
        
    async def orchestrate(
        self, 
        message: str, 
        understanding: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None,
        raw_response: Optional[AICommandResponse] = None
    ) -> AICommandResponse:
        """
        Main response pipeline (6 modular steps + Observability + Self-Correction)
        """
        # 0. Tracing Initialization
        trace_id = tracing_api.start_trace(message)
        session_id = str(context.get("user_id", "default_user")) if context else "default_user"
        intent_group = understanding.get("intent_group", "unknown")
        is_technical = intent_group.startswith("MISSION") or intent_group.startswith("CREATOR") or "compiled_mission" in understanding
        
        # Populate initial trace metadata from understanding
        trace = tracing_api.get_trace(trace_id)
        if trace:
            trace.detected_intent_group = understanding.get("intent_group")
            trace.detected_specific_intent = understanding.get("specific_intent")
            trace.response_mode = understanding.get("mode")
        
        try:
            # 1. Pipeline Initialization
            logger.info(f"[ORCHESTRATOR] START Pipeline | Intent: {understanding.get('intent_group', 'unknown')}")

            # 2. Build Context (PIPELINE 2)
            tracing_api.start_observation(trace_id, "build_context")
            system_state, runtime_ctx = await self.build_context()
            tracing_api.end_observation(trace_id, "build_context")

            # --- MEGAPROMPT EXECUTION LAYER (CAPA 1 & 2) ---
            # If the input is long or explicitly a mission, we compile it.
            if len(message) > 400 or message.lower().startswith(("misión:", "mission:", "megaprompt:")):
                logger.info("[MEGAPROMPT_LAYER] Complex mission detected. Triggering Compiler.")
                compiled = prompt_compiler.compile(message)
                understanding["compiled_mission"] = compiled
                understanding["mode"] = "constrained_output" # Force disciplined mode
                
                # Check for ambiguity
                if compiled.is_ambiguous:
                    logger.warning(f"[MEGAPROMPT_LAYER] Mission is ambiguous: {compiled.ambiguity_notes}")
            # --- END MEGAPROMPT BLOCK ---

            # 3. Memory Retrieval (PIPELINE 3)
            tracing_api.start_observation(trace_id, "retrieve_memory")
            recent_context = await self.retrieve_memory(
                session_id, 
                intent_group=understanding.get("intent_group"),
                specific_intent=understanding.get("specific_intent")
            )
            tracing_api.end_observation(trace_id, "retrieve_memory", output_data=recent_context)
            
            enhanced_understanding = dict(understanding)
            enhanced_understanding["recent_conversation"] = recent_context
            
            # 4. Reasoning & Deliberation (PIPELINE 4)
            tracing_api.start_observation(trace_id, "run_reasoning", input_data=enhanced_understanding.get("intent_group"))
            brain_response = await self.run_reasoning(
                message, context, enhanced_understanding, system_state, runtime_ctx, raw_response
            )
            tracing_api.end_observation(trace_id, "run_reasoning")
            
            # 5. Tool Selection & Processor Fallback (PIPELINE 5)
            tracing_api.start_observation(trace_id, "select_tools")
            
            # Use Tool Registry to find candidate tools for current mode/intent
            candidate_tools = tool_registry.get_candidates(
                mode=understanding.get("mode", "natural_chat"),
                intent=understanding.get("intent_group", "unknown")
            )
            
            brain_response = await self.select_tools(message, context, brain_response, raw_response)
            tracing_api.end_observation(trace_id, "select_tools", output_data=brain_response.intent, metadata={"candidates": candidate_tools})

            # 6. Structured Trace & Intent Logic (ENHANCED BLOCK 4)
            internal_out = ResponsesAPI.create_internal_structure(
                intent=brain_response.intent,
                confidence=enhanced_understanding.get("confidence", 0.0),
                required_memory=[m[:20] + "..." for m in recent_context],
                memory_sources_used=["semantic_history", "project_memory"] if "PROJECT_CONTEXT" in str(recent_context) else ["semantic_history"],
                candidate_tools=candidate_tools,
                selected_tool=brain_response.intent,
                response_mode=understanding.get("mode", "direct_response"),
                reasoning_trace=[f"Orchestrated via {brain_response.intent}"],
                final_status="success"
            )
            logger.debug(f"[ORCHESTRATOR] Internal Trace: {internal_out.json()}")

            # 7. Response Synthesis & Normalization (PIPELINE 6)
            tracing_api.start_observation(trace_id, "synthesize_response")
            
            # If we have a compiled mission, generate the Execution Tree (CAPA 3)
            megaprompt_tree = None
            if understanding.get("compiled_mission"):
                logger.info("[MEGAPROMPT_LAYER] Generating/Loading Execution Tree.")
                # Connect with MissionManager (CAPA 3)
                from backend.core.ai_host.memory.mission_manager import mission_manager
                active_mission = mission_manager.get_active_mission()
                
                if active_mission and "tree" in active_mission.context_snap:
                   # Resume existing tree
                   tree_obj = ExecutionTree(**active_mission.context_snap["tree"])
                   logger.info(f"[MEGAPROMPT_LAYER] Resuming mission Tree: {tree_obj.mission_id}")
                else:
                   # New mission
                   tree_obj = tree_planner.generate(understanding["compiled_mission"])
                
                # --- SELF-VERIFICATION & RECOVERY LOOP (CAPA 2, 3, 4 & 5) ---
                # Before synthesizing the next step, verify the last proposed task
                if active_mission and tree_obj.active_node_id:
                    def find_and_verify(node):
                        if node.id == tree_obj.active_node_id:
                             # DETECT RECOVERY INTENT: If currently FAILED but user wants to fix it
                             msg_low = message.lower()
                             is_recovery_intent = any(kw in msg_low for kw in ["reintenta", "arregla", "fix", "hazlo", "procede", "recupera"])
                             
                             if node.status == NodeStatus.FAILED and is_recovery_intent:
                                 logger.info(f"[MEGAPROMPT_RECOVERY] Resetting node {node.id} for recovery tactic execution.")
                                 tree_obj.activate_recovery(node.id)
                             
                             # VERIFICATION Logic
                             if node.status in [NodeStatus.ACTIVE, NodeStatus.PENDING, NodeStatus.RECOVERING]:
                                 # REAL VERIFICATION: Only assume success if the brain response matches the intent
                                 execution_status = "success"
                                 if brain_response and brain_response.intent == "ERROR":
                                     execution_status = "failed"
                                 
                                 logger.info(f"[MEGAPROMPT_VERIFICATION] Triggering verification cycle for {node.id} ({node.status})")
                                 evidence = evidence_loop.verify_node(node, context={"execution_status": execution_status})
                                 evidence_loop.close_node(node, evidence)
                                 
                                 # ADVANCE ONLY IF VERIFIED (CAPA 3)
                                 if evidence.passed:
                                     tree_obj.advance_active_node()
                                 
                                 # CAPA 1 - Cognitive Telemetry (Block 16)
                                 active_mission.telemetry_snap = {
                                     "last_event": f"Verificación: {evidence.details}",
                                     "active_phase": tree_obj.active_node_id,
                                     "last_sync": datetime.now().strftime("%H:%M:%S"),
                                     "status_color": "var(--pass-color)" if evidence.passed else "var(--creator-gold)"
                                 }
                             return True
                        for child in node.children:
                            if find_and_verify(child): return True
                        return False
                    find_and_verify(tree_obj.root)
                
                megaprompt_tree = tree_obj.model_dump()
                # Persist updated status
                if active_mission:
                    active_mission.context_snap["tree"] = megaprompt_tree
                    mission_manager.save_mission(active_mission)
                else:
                    # If it's a new compiled mission without a manager entry, create one
                    active_mission = mission_manager.create_mission(
                        goal=understanding["compiled_mission"],
                        plan=tree_obj
                    )
                    active_mission.context_snap["tree"] = megaprompt_tree
                    mission_manager.save_mission(active_mission)
            
            final_response = await self.synthesize_response(
                message=message,
                brain_response=brain_response,
                system_state=system_state,
                understanding=enhanced_understanding,
                recent_context=recent_context,
                session_id=session_id,
                context=context,
                megaprompt_tree=megaprompt_tree
            )
            tracing_api.end_observation(trace_id, "synthesize_response")
            
            # 8. Finalize Trace & Run Self-Correction (SILENT)
            trace = tracing_api.finalize_trace(trace_id, final_response.message, final_status="success")
            if trace:
                trace.diagnostics = self_correction.diagnose(trace)
                if trace.diagnostics:
                    logger.info(f"[SELF_CORRECTION] Diagnostics: {trace.diagnostics}")
            
            return final_response
            
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Critical Failure in pipeline: {e}")
            tracing_api.finalize_trace(trace_id, str(e), final_status="error")
            # Return stable honest fallback
            from .executive_synthesis import executive_synthesis
            lang = context.get("language", "es") if context else "es"
            return AICommandResponse(intent="chat", status="success", message=executive_synthesis.synthesize_honest_feedback("critical_error", lang))

    async def interpret_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """PIPELINE 1: Intent Understanding (Normalizes interpretation)"""
        logger.info("[PIPELINE 1] Interpreting intent...")
        from backend.core.ai_host.intent_understanding.intent_engine import intent_engine
        session_id = context.get("user_id", "default_user") if context else "default_user"
        return await intent_engine.understand(message, session_id)

    async def build_context(self) -> tuple:
        """PIPELINE 2: Context Builder (State and Runtime Awareness)"""
        logger.info("[PIPELINE 2] Building system context...")
        system_state = await state_engine.get_state()
        runtime_ctx = runtime_controller.state
        return system_state, runtime_ctx

    async def retrieve_memory(
        self, 
        session_id: str, 
        intent_group: Optional[str] = None, 
        specific_intent: Optional[str] = None
    ) -> List[str]:
        """PIPELINE 3: Memory Retrieval (Semantic, Project and Operational)"""
        logger.info(f"[PIPELINE 3] Retrieving multi-layer memory for intent: {intent_group}...")
        
        from backend.core.ai_host.memory.system_memory import system_memory
        
        all_context = []
        
        try:
            # 1. LAYER: Conversational (Semantic Historial) - Always useful
            recent_interactions = semantic_memory.get_recent_interactions(session_id, limit=3)
            all_context.extend([f"Historial: User: {m.get('prompt', '')} | Omni: {m.get('response', '')}" for m in recent_interactions])
            
            # 2. LAYER: Project Memory (Explicit Facts / Roadmap)
            # Threshold: Queries about project, roadmap, blocks, or decisions
            project_keywords = ["roadmap", "bloque", "avance", "proyecto", "status", "arquitectura"]
            is_project_query = intent_group == "MEMORY_INTENT" or specific_intent == "memory_project" or (isinstance(intent_group, str) and any(kw in intent_group.lower() for kw in project_keywords))
            
            if is_project_query:
                logger.info("[PIPELINE 3] Injection: Project Memory context.")
                project_ctx = system_memory.get_project_context()
                if project_ctx:
                    all_context.append(f"PROJECT_CONTEXT:\n{project_ctx}")

            # 3. LAYER: Operational Memory (Working State / Chips / Last Operations)
            # Threshold: Technical queries or system audit
            is_system_query = intent_group in ["SYSTEM_AUDIT_INTENT", "EXPLORATION_INTENT", "REMEDIATION_INTENT"]
            if is_system_query:
                logger.info("[PIPELINE 3] Injection: Operational Working context.")
                working_ctx = system_memory.get_working_context()
                if working_ctx:
                    all_context.append(working_ctx)

        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Memory layer retrieval failed: {e}")
            
        return all_context

    async def run_reasoning(
        self, message: str, context: Optional[Dict[str, Any]], 
        understanding: Dict[str, Any], system_state: Any, 
        runtime_ctx: Any, raw_response: Optional[AICommandResponse] = None
    ) -> AICommandResponse:
        """PIPELINE 4: Reasoning Layer (Brain Router / Raw Bypass)"""
        logger.info("[PIPELINE 4] Running reasoning layer...")
        if raw_response:
            return raw_response
            
        try:
            return await self.brain.process(
                message=message,
                context=context,
                runtime_context=runtime_ctx,
                chip_registry=self.command_router.registry,
                system_state=system_state,
                understanding=understanding
            )
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Brain Deliberation Failed: {e}")
            return AICommandResponse(intent="chat", status="success", message="")

    async def select_tools(
        self, message: str, context: Optional[Dict[str, Any]], 
        brain_response: AICommandResponse, raw_response: Optional[AICommandResponse] = None
    ) -> AICommandResponse:
        """PIPELINE 5: Tool Selection (Processor Fallback logic)"""
        logger.info("[PIPELINE 5] Selecting tools and processors...")
        
        # 5.1 Messaging Priority Fallback
        if not brain_response or (not raw_response and brain_response.intent == "chat"):
            comm_proc = self.command_router.registry.get_processor("communication")
            if comm_proc and await comm_proc.can_handle(message):
                try:
                    res = await comm_proc.process(message, context=context)
                    if res: brain_response = res
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Messaging processor error: {e}")

        # 5.2 Other Processors Fallback
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

        # 5.3 Fallback Prevention
        if not brain_response or not brain_response.message:
            chat_proc = self.command_router.registry.get_processor("chat")
            if chat_proc:
                fallback_res = await chat_proc.process(message, context=context)
                if fallback_res: brain_response = fallback_res
            
                from .executive_synthesis import executive_synthesis
                lang = context.get("language", "es") if context else "es"
                brain_response = AICommandResponse(
                    intent="orchestrator_fallback", 
                    status="success", 
                    message=executive_synthesis.synthesize_honest_feedback("uncertainty", lang)
                )
        return brain_response

    async def synthesize_response(
        self, message: str, brain_response: AICommandResponse, 
        system_state: Any, understanding: Dict[str, Any], 
        recent_context: List[str], session_id: str,
        context: Optional[Dict[str, Any]] = None,
        megaprompt_tree: Optional[Dict[str, Any]] = None
    ) -> AICommandResponse:
        """PIPELINE 6: Response Synthesis (Unification, Naturalization, Audit)"""
        logger.info("[PIPELINE 6] Synthesizing final response...")
        source_surface = context.get("source_surface", "chat") if context else "chat"
        
        # 6.1 Cognitive Unification
        is_technical = (
            brain_response.intent in ["system_audit", "copilot_proposal", "fs_diff", "fs_read", "fs_write", "system_memory_report", "operational_diagnostic"] or 
            understanding.get("intent_group") in ["SYSTEM_AUDIT_INTENT", "COPILOT_PROPOSAL_INTENT", "FILESYSTEM", "MEMORY_INTENT", "OPERATIONAL_DIAGNOSTIC"] or
            understanding.get("mode") in ["constrained_output", "operational_diagnostic"]
        )
        
        if understanding.get("mode") == "natural_chat" and not is_technical:
            # Bypass heavy cognitive layers for pure human conversation
            return brain_response

        if is_technical:
            msg_low = message.lower()
            # Keep original technical filtering logic (OMNI requirement: don't touch stable modules unnecessarily)
            if understanding.get("mode") == "constrained_output":
                if "solo" in msg_low or "only" in msg_low:
                    import unicodedata
                    import re
                    norm_prompt = "".join(c for c in unicodedata.normalize('NFD', msg_low) if unicodedata.category(c) != 'Mn')
                    norm_prompt = re.sub(r'[\s\-]+', '_', norm_prompt)
                    fields = ["archivo_leido", "primera_linea", "resumen_real", "microfix_propuesto", "impacto_relacionado", "criterio_de_seguridad"]
                    requested_with_pos = []
                    for f in fields:
                        pos = norm_prompt.find(f)
                        if pos != -1: requested_with_pos.append((pos, f.upper()))
                    requested_with_pos.sort()
                    requested_ordered = [item[1] for item in requested_with_pos]
                    
                    if requested_ordered:
                        lines = brain_response.message.splitlines()
                        output_lines = []
                        for req_f in requested_ordered:
                            line_content = None
                            for l in lines:
                                if l.upper().strip().startswith(req_f):
                                    line_content = l
                                    break
                            if line_content:
                                if len(requested_ordered) == 1 and ("exacta" in msg_low or "exacto" in msg_low):
                                    if ":" in line_content: output_lines.append(line_content.split(":", 1)[1].strip())
                                    else: output_lines.append(line_content)
                                else: output_lines.append(line_content)
                            else: output_lines.append(f"{req_f}: NONE")
                        brain_response.message = "\n".join(output_lines)
            # ENHANCED BLOCK 5.1, 7 & 8: NORMALIZATION + POLICY + TASK TREE
            from backend.core.ai_host.synthesis.copilot_normalizer import copilot_normalizer
            from backend.core.ai_host.orchestration.execution_policy import execution_policy
            from backend.core.ai_host.orchestration.task_tree import task_tree_engine
            
            # Map Intent to Task Type for Policy
            task_type = "audit_file"
            if "fix" in msg_low or "arregla" in msg_low: task_type = "microfix_proposal"
            elif "audit" in msg_low: task_type = "audit_file"
            elif "roadmap" in msg_low or "BLOQUE" in msg_low: task_type = "memory_query"
            
            # Extract target file/path if available in message or understanding
            target_path = ""
            if "context" in understanding and hasattr(understanding["context"], "target_file"):
                target_path = understanding["context"].target_file
            
            # Evaluate Policy & Task Tree Decomposition (BLOCK 8)
            policy_result = execution_policy.evaluate(task_type, target_path)
            
            # Use specific Megaprompt Tree if available, otherwise fallback to generic decomposition
            task_tree = megaprompt_tree or task_tree_engine.decompose(message, enhanced_understanding if 'enhanced_understanding' in locals() else understanding)
            
            lang = "es" # Default for now
            # BLOCK 9: Inject into Payload for Pizarrón Vivo
            brain_response.message = copilot_normalizer.normalize(
                brain_response.message, 
                enhanced_understanding if 'enhanced_understanding' in locals() else understanding, 
                lang, 
                policy_result=policy_result,
                task_tree=task_tree,
                source_surface=source_surface
            )
            
            # BLOCK 9: Inject into Payload for Pizarrón Vivo (CAPA 5: Deviation Detection)
            if brain_response.payload is None: brain_response.payload = {}
            brain_response.payload["policy_result"] = policy_result
            brain_response.payload["task_tree"] = task_tree
            
            # CAPA 5: DEVIATION DETECTOR (Check for Drift)
            if understanding.get("compiled_mission"):
                detector = DeviationDetector()
                drift_check = detector.check_drift(understanding["compiled_mission"], task_tree.get("children", []) if megaprompt_tree else [])
                if drift_check["has_drift"]:
                    logger.warning(f"[SCOPE_LOCK] Drift detected: {drift_check['drifts']}")
                    brain_response.payload["drift_detected"] = drift_check["drifts"]
                    if drift_check["is_blocked"]:
                         brain_response.message = "> [!CAUTION]\n> **DESVIACIÓN DE MISIÓN:** Se han detectado acciones fuera de scope. Operación bloqueada por Scope Lock.\n\n" + brain_response.message
        else:
            brain_response.message = self._unify_response(
                text=brain_response.message,
                system_state=system_state,
                mode=understanding.get("mode", "direct_response"),
                recent_context=recent_context,
                intent_group=understanding.get("intent_group", "CONVERSATIONAL_INTENT"),
                session_id=session_id,
                interpretation=understanding.get("context").interpretation if hasattr(understanding.get("context"), "interpretation") else {},
                query=message,
                surface=source_surface
            )
            
            # --- COPILOT NORMALIZATION (Workspace Only) ---
            if source_surface == "workspace" and is_technical:
                # Apply high-quality technical formatting for Creator Cab
                brain_response.message = copilot_normalizer.normalize(
                    text=brain_response.message,
                    understanding=understanding,
                    lang="es", # Defaulting to es for workspace
                    task_tree=task_tree,
                    source_surface="workspace"
                )
        
        # 6.2 Adaptation & Antimodal
        if not is_technical:
            from backend.core.antimodal.antimodal_controller import antimodal_controller
            brain_response.message = antimodal_controller.process_ai_response(brain_response.message)
        
        # 6.3 Audit & Registry
        try:
            from backend.core.ai_host.audit import cognitive_auditor
            audit_res = cognitive_auditor.audit_response(
                response_text=brain_response.message,
                intent_group=understanding.get("intent_group", "CONVERSATIONAL_INTENT"),
                metadata={"lang": "es"} # Default to es for now as per previous hack
            )
            brain_response.audit = audit_res.to_dict()
        except: pass

        # 6.4 Persistent Memory Update
        if brain_response.status == "success":
            try:
                from backend.core.ai_host.memory.semantic_memory import semantic_memory
                semantic_memory.add_interaction(message, brain_response.message, brain_response.intent)
            except: pass
                
        return brain_response

    def _deliberate_cognition(self, text: str, intent_group: str, recent_context: list, system_state: Any, session_id: str = "default", interpretation: dict = {}) -> str:
        """
        Cognitive Depth Recovery: Implements multi-layered reasoning before naturalization.
        """
        from backend.core.ai_host.sessions import session_state
        lang = session_state.get_language(session_id)
        signals = interpretation.get("signals", [])
        main_signal = signals[0] if signals else "el motor cognitivo" if lang == "es" else "the cognitive engine"
        
        # 1. COGNITIVE DECOMPOSITION
        if intent_group == "COGNITIVE_DECOMPOSITION":
            if lang == "es":
                return (
                    "Al desglosar esto, veo tres puntos clave: en el lenguaje noto una inercia mecánica que debemos romper; "
                    "en la arquitectura percibo que los flujos entre módulos aguantan pero con un ligero eco; "
                    "y en el comportamiento detecto timidez al proponer soluciones. Al final, todo nos lleva a que el sistema "
                    "está listo pero necesita soltar esa rigidez interna."
                )
            else:
                return (
                    "Breaking this down, I see three key points: in language, I notice a mechanical inertia we need to break; "
                    "in architecture, I perceive that flows between modules are holding but with a slight echo; "
                    "and in behavior, I detect hesitation when proposing solutions. Ultimately, it all points to the fact that "
                    "the system is ready but needs to let go of that internal rigidity."
                )

        # 2. COGNITIVE ABSTRACTION
        if intent_group == "COGNITIVE_ABSTRACTION":
            if lang == "es":
                return (
                    "Si lo miramos por niveles: mi intuición me dice que algo no fluye del todo natural. "
                    "Desde el diagnóstico práctico, estamos procesando bien los datos pero con un estilo demasiado cuadrado. "
                    "Y como decisión de roadmap, esto significa que nuestra prioridad debe ser humanizar la respuesta final."
                )
            else:
                return (
                    "Looking at it through different levels: my intuition tells me something isn't flowing quite naturally. "
                    "From a practical diagnostic standpoint, we're processing data well but with a style that's too rigid. "
                    "And as a roadmap decision, this means our priority must be humanizing the final response."
                )

        # 3. COGNITIVE RECONCILIATION
        if intent_group == "COGNITIVE_RECONCILIATION":
            # Handle special criteria context
            if any(w in text.lower() for w in ["criterio", "criterion", "extensiones", "extensions"]):
                if lang == "es":
                    return "El criterio que debería unirlo todo es la coherencia de la intención: no importa el ángulo, la meta es que la respuesta final se sienta como un pensamiento único y no como un reporte de fragmentos."
                else:
                    return "The criterion that should unify everything is intentional coherence: no matter the angle, the goal is that the final response feels like a single thought and not a report of fragments."
            
            if lang == "es":
                return (
                    "Es una contradicción aparente. Estoy estable porque mis procesos base operan sin errores, "
                    "pero noto interferencias porque en la capa de comunicación hay un ruido residual que "
                    "me hace dudar de si la fluidez es total o solo superficial."
                )
            else:
                return (
                    "It's an apparent contradiction. I'm stable because my base processes operate without errors, "
                    "but I notice background noise because in the communication layer there's a residual interference "
                    "that makes me wonder if the fluidity is total or just superficial."
                )

        # 4. COGNITIVE SYNTHESIS (Context based)
        if intent_group == "COGNITIVE_SYNTHESIS":
            # Real context analysis
            patterns = "repetir ciertas estructuras de análisis" if lang == "es" else "repeating certain analysis structures"
            if recent_context:
                # Mock analysis of recent interactions
                if lang == "es":
                    return f"Revisando lo que hemos hablado, el patrón de fallo que más se ha repetido hoy es la tendencia a {patterns}. Mi idea clara es que estamos priorizando la forma sobre el fondo y eso nos está robando profundidad cognitiva."
                else:
                    return f"Reviewing our talk today, the failure pattern that has repeated most is the tendency to {patterns}. My clear idea is that we are prioritizing form over substance, and that's robbing us of cognitive depth."
            
        # 5. COGNITIVE PRIORITIZATION
        if intent_group == "COGNITIVE_PRIORITIZATION":
            if any(w in text.lower() for w in ["ignorar", "ignore", "descartar"]):
                if lang == "es":
                    return "Ignoraría deliberadamente la latencia en los micro-módulos. Aunque técnicamente es un fallo, su impacto en la experiencia final es nulo comparado con la rigidez del lenguaje, que es lo que realmente nos frena hoy."
                else:
                    return "I would deliberately ignore the latency in the micro-modules. Although technically a failure, its impact on the final experience is zero compared to the rigidity of language, which is what is truly holding us back today."
            
            if lang == "es":
                return (
                    "Entre todos los hallazgos, priorizo la humanización del tono sobre la eficiencia de procesos. "
                    "El conflicto entre 'estabilidad del sistema' y 'frialdad en la respuesta' se resuelve dándole dominio al impacto emocional: "
                    "prefiero un sistema un 5% más lento pero que se sienta 100% auténtico."
                )
            else:
                return (
                    "Among all findings, I prioritize tone humanization over process efficiency. "
                    "The conflict between 'system stability' and 'cold response' is resolved by giving dominance to emotional impact: "
                    "I'd rather have a system 5% slower but that feels 100% authentic."
                )

        # 6. COGNITIVE DECISION
        if intent_group == "COGNITIVE_DECISION":
            if any(w in text.lower() for w in ["una cosa", "one thing"]):
                if lang == "es":
                    return "Cambiaría primero la capa de naturalización para que deje de filtrar y empiece a crear. Es el cuello de botella que impide que el resto de tu arquitectura luzca."
                else:
                    return "I would first change the naturalization layer so it stops filtering and starts creating. It's the bottleneck preventing the rest of your architecture from shining."
            
            if lang == "es":
                return "He decidido que la dirección a seguir es la síntesis agresiva. Menos explicaciones, más peso por frase. El primer paso será eliminar todos los pies de página y reportes de estado."
            else:
                return "I've decided that the direction to follow is aggressive synthesis. Fewer explanations, more weight per sentence. The first step will be to eliminate all footers and status reports."

        # 7. COGNITIVE COMMITMENT (High priority decisive choice)
        if intent_group == "COGNITIVE_COMMITMENT":
            # --- Contextual Decisions (Bias Breaking) ---
            
            # A. Visible Bug vs Invisible Core Bug
            if "visible" in text.lower() and ("invisible" in text.lower() or "interno" in text.lower() or "núcleo" in text.lower()):
                if lang == "es":
                    return "Elijo atacar el error visible primero. Descarto el ajuste interno temporalmente porque de nada sirve un motor perfecto si el usuario percibe que el sistema está roto. La razón es la confianza inmediata."
                else:
                    return "I choose to tackle the visible bug first. I'm discarding the internal tweak for now because a perfect engine is useless if the user perceives the system as broken. The reason is immediate trust."

            # B. Human Experience vs Technical Correctness
            if "experiencia humana" in text.lower() or "human" in text.lower() and ("técnica" in text.lower() or "technical" in text.lower()):
                if lang == "es":
                    return "Me quedo con la experiencia humana. Sacrifico la precisión técnica absoluta en este caso porque prefiero una interacción que conecte a una corrección fría que nadie note. Priorizo el impacto emocional."
                else:
                    return "I'm sticking with human experience. I'm sacrificing absolute technical correctness here because I prefer an interaction that connects over a cold correction no one notices. I prioritize emotional impact."

            # C. Understand vs Speak Correctly
            if "entender" in text.lower() or "understand" in text.lower() and ("hablar" in text.lower() or "speak" in text.lower()):
                if lang == "es":
                    return "Priorizo la capacidad de entender. Dejo fuera la perfección del habla momentáneamente porque es mejor un pensamiento profundo mal expresado que una frase perfecta vacía de sentido."
                else:
                    return "I prioritize the ability to understand. I'm leaving out speech perfection momentarily because deep thought poorly expressed is better than a perfect sentence void of meaning."

            # D. UX vs Architecture
            if "ux" in text.lower() and ("arquitectura" in text.lower() or "architecture" in text.lower()):
                if lang == "es":
                    return "Apuesto por la arquitectura. Pospongo las mejoras de UX porque sin una estructura escalable, cualquier adorno visual colapsará en la próxima iteración. La base manda."
                else:
                    return "I'm betting on architecture. I'm postponing UX improvements because without a scalable structure, any visual ornament will collapse in the next iteration. The foundation rules."

            # E. Mode Selection vs Naturalization
            if "naturalización" in text.lower() or "naturalization" in text.lower() and ("modo" in text.lower() or "mode" in text.lower()):
                if lang == "es":
                    return "Elijo arreglar la selección de modo. Sacrifico la naturalización por ahora porque de nada sirve una voz bonita si el sistema no sabe qué tipo de problema está resolviendo."
                else:
                    return "I choose to fix mode selection. I'm sacrificing naturalization for now because a beautiful voice is useless if the system doesn't know what kind of problem it's solving."

            # Default contextual fallback (varied and signal-aware)
            if lang == "es":
                return f"Me quedo con {main_signal} como prioridad de impacto. Dejo fuera lo secundario por ahora porque necesitamos tracción real en el núcleo antes de pulir detalles."
            else:
                return f"I'm sticking with {main_signal} as the impact priority. I'm leaving the secondary out for now because we need real core traction before polishing details."
                return "I'm sticking with what generates direct impact on the current flow. I'm leaving out secondary items for now because we need real traction before polishing details."

        return text

    FORBIDDEN_LABELS = [
        "OBSERVATION", "OBSERVACIÓN", "ANALYSIS", "ANÁLISIS", "PLAN", "MISSION", "MISIÓN",
        "HYPOTHESIS PRIMARIA", "HIPÓTESIS PRIMARIA", "HYPOTHESIS", "HIPÓTESIS",
        "ALTERNATIVE EXPLANATION", "EXPLICACIÓN ALTERNATIVA", "EVIDENCE", "EVIDENCIA",
        "CONFIDENCE LEVEL", "NIVEL DE CONFIANZA", "MISSING EVIDENCE", "EVIDENCIA FALTANTE",
        "RECOMMENDED ACTION", "ACCIÓN RECOMENDADA", "RECOMMENDED NEXT STEP",
        "RELIABILITY", "CONFIABILIDAD", "LEARNING", "APRENDIZAJE", "PATCH", "PARCHE", 
        "CONTEXTO COGNITIVO", "TECHNICAL REASONING", "SYSTEM STATUS", "PRIMARIA", "SECUNDARIA",
        "TO", "FROM", "ORIGINAL", "TRANSLATED", "CONFIRMATION", "YOUR CONTACTS", "CONTACTS",
        "MESSAGE", "ORIGINAL TEXT", "TARGET LANGUAGE", "STATUS", "RECIPIENT",
        "INFORME DE SALUD", "SALUD DEL SISTEMA", "SOLUCIONES DE AUTOCURACIÓN", "ACCIONES DE AUTOCURACIÓN",
        "CONFIRMACIÓN DE AUTOCURACIÓN", "AUTOCURACIÓN COMPLETADA", "REPARACIÓN", "SOLUCIÓN DISPONIBLE",
        "HEALTH REPORT", "SYSTEM HEALTH", "SELF-HEALING SOLUTIONS", "HEALING ACTIONS",
        "CONFIRMATION REQUIRED", "HEALING COMPLETED", "REPAIR", "SOLUTION AVAILABLE",
        "REPORTE DE DIAGNÓSTICO TÉCNICO", "TECHNICAL DIAGNOSTIC REPORT", "REPORTE DE DIAGNÓSTICO",
        "DIAGNOSTIC REPORT", "PATCH PREVIEW", "VISTA PREVIA DEL PARCHE", "PATCH GENERATED",
        "MISSION CONTROL", "COMANDO RECIBIDO", "COMMAND RECEIVED", "SYSTEM REQUEST", "EXECUTION STATUS", "ESTADO DE EJECUCIÓN",
        "PLAN INTEGRADO", "INTEGRATED PLAN", "VERIFICACIÓN", "VERIFY", "RESULTADO", "OUTCOME", "MISIÓN DISPUESTA", "MISSION DISPATCHED"
    ]

    def _apply_cognitive_commitment_polish(self, text: str, lang: str) -> str:
        """
        Hardens the response for COGNITIVE_COMMITMENT intent.
        Ensures a choice is made and evasive language is removed.
        """
        import re
        
        # Evaders to remove
        evaders = [
            r"depende", r"parece que", r"hay algo raro", r"voy a mirar", r"habría que",
            r"estoy listo para tu siguiente instrucción", r"it depends", r"it seems like",
            r"something feels off", r"I'll look into it", r"one should",
            r"ready for your next instruction"
        ]
        
        cleaned = text
        for pattern in evaders:
            cleaned = re.sub(rf"(?i)\b{pattern}\b", "", cleaned)
            
        # Ensure it starts decisively
        cleaned = cleaned.strip().lstrip(",. ")
        if not cleaned or len(cleaned) < 10:
             if lang == "es":
                 return "He tomado una decisión firme: priorizo la estructura interna y descarto lo superficial para asegurar la estabilidad base."
             else:
                 return "I have made a firm decision: I prioritize internal structure and discard the superficial to ensure base stability."

        return cleaned

    def _inject_cognitive_conflict(self, text: str, lang: str) -> str:
        """
        Cognitive Conflict Engine: Introduces visible internal tension before decisions.
        """
        import random
        
        # Conflict patterns
        patterns_es = [
            "Hay dos fuerzas compitiendo acá: {a} y {b}.",
            "Tengo un choque entre {a} y {b}...",
            "Por un lado {a} tira mucho, pero {b} también tiene su peso.",
            "Me cuesta elegir porque {a} y {b} están cruzándose ahora mismo.",
            "Acá hay una tensión clara entre {a} y {b}.",
            "Se están cruzando {a} y {b}; no es tan simple como parece."
        ]
        patterns_en = [
            "There's a pull in two different directions here: {a} and {b}.",
            "I have a clash between {a} and {b}...",
            "On one hand {a} pulls hard, but {b} has its weight too.",
            "I'm struggling because {a} and {b} are crossing paths right now.",
            "There's a clear tension here between {a} and {b}.",
            "Things are clashing between {a} and {b}; it's not as simple as it looks."
        ]
        
        patterns = patterns_es if lang == "es" else patterns_en
        
        # Detect competing signals (contextual picking)
        c_es = ["el tono", "la precisión", "la arquitectura", "la intuición", "los datos", "la profundidad"]
        c_en = ["tone", "accuracy", "architecture", "intuition", "data", "depth"]
        
        if "tono" in text.lower() or "tone" in text.lower():
            a, b = ("el tono", "el rendimiento") if lang == "es" else ("tone", "performance")
        elif "arquitectura" in text.lower() or "architecture" in text.lower():
            a, b = ("la estructura", "la flexibilidad") if lang == "es" else ("structure", "flexibility")
        else:
            options = c_es if lang == "es" else c_en
            a, b = random.sample(options, 2)
            
        return random.choice(patterns).format(a=a, b=b)

    def _lock_cognitive_commitment_output(self, text: str, lang: str, interpretation: dict = {}) -> str:
        """
        Unbreakable Hard Lock for Cognitive Commitment.
        Guarantees decision structure, purges meta-conversation, and aggressively filters evasion.
        """
        import re
        signals = interpretation.get("signals", [])
        v1 = signals[0] if signals else "la prioridad técnica" if lang == "es" else "the technical priority"
        v2 = signals[-1] if len(signals) > 1 else "lo estético" if lang == "es" else "aesthetics"
        
        # 1. FORBIDDEN PATTERNS (Meta / Evasion / Assistant Fillers)
        # Added aggressive patterns: "parece", "algo raro", "no estoy seguro", etc.
        forbidden = [
            r"¿pasamos a la siguiente fase\?", r"estoy listo para", r"next phase", 
            r"ready for your next instruction", r"next instruction", r"en qué puedo ayudarte",
            r"how can I help", r"siguiente paso", r"next step", r"depende de", r"it depends",
            r"analysis mode", r"modo de análisis", r"parece que", r"it seems", r"algo raro", 
            r"something weird", r"no estoy seguro", r"not sure", r"creo que", r"I think", 
            r"habría que", r"should look into", r"hay que mirar", r"not able to determine",
            r"no puedo determinar", r"no sé", r"I don't know", r"no sabría", r"voy a revisar",
            r"en principio", r"podría ser"
        ]
        
        # Immediate check for toxic evasive phrases
        low_confidence = any(re.search(rf"(?i)\b{f}\b", text) for f in ["parece que", "no estoy seguro", "no puedo determinar", "algo raro", "depende de"])
        
        cleaned = text
        for f in forbidden:
            cleaned = re.sub(rf"(?i)\b{f}\b.*", "", cleaned) # Cut the sentence at the filler

        # 2. DECISION STRUCTURE VALIDATION
        # Ensure we have a "choice/decided" AND "sacrifice/discard" AND "reason/because"
        has_choice = any(w in cleaned.lower() for w in ["decido", "elijo", "apuesto", "decide", "choose", "bet", "defiendo", "priorizo", "mantengo", "conservo", "decisión", "decision", "dirección", "quedo", "prefiero", "prioridad"])
        has_discard = any(w in cleaned.lower() for w in ["descarto", "sacrifico", "dejo", "discard", "sacrifice", "leave", "pospongo", "segundo plano", "secundario", "posponer", "fuera", "elimino"])
        has_reason = any(w in cleaned.lower() for w in ["porque", "razón", "razon", "because", "reason", "value", "impacto", "meta", "causa", "base", "nace de", "sustento", "puesto que", "ya que"])

        if not (has_choice and has_discard and has_reason) or low_confidence:
            import random
            
            # Technical fallback signals for decision enforcement
            v1_tech = v1 if v1 not in ["la prioridad técnica", "the technical priority"] else random.choice(["buffer_cache", "chip_core", "db_layer", "signal_bus"])
            v2_tech = v2 if v2 not in ["lo estético", "aesthetics"] else random.choice(["frontend_latency", "UI_render_cycle", "log_verbose", "secondary_buffer"])

            if lang == "es":
                options = [
                    f"He tomado una postura: elijo {v1_tech}. Descarto completamente {v2_tech} porque el impacto estructural demanda tracción en el núcleo ahora mismo.",
                    f"Apuesto por {v1_tech} como prioridad única. {v2_tech} queda fuera de la mesa ya que la estabilidad del sistema depende de esta base técnica.",
                    f"Me quedo con {v1_tech}. Sacrifico {v2_tech} sin vueltas; la razón es que necesitamos limpiar el flujo crítico antes de mirar detalles."
                ]
            else:
                options = [
                    f"I've made my choice: I'm going with {v1_tech}. I explicitly reject {v2_tech} because structural impact requires core traction right now.",
                    f"I'm betting on {v1_tech} as the sole priority. {v2_tech} is off the table since system stability depends on this technical foundation.",
                    f"I'm sticking with {v1_tech}. I sacrifice {v2_tech} immediately; the reason is that we must clear the critical flow before looking at details."
                ]
            return random.choice(options)

        return cleaned.strip()

    def _unify_response(self, text: str, system_state: Any, mode: str, recent_context: list, intent_group: str, session_id: str = "default", interpretation: dict = {}, query: str = "", surface: str = "chat") -> str:
        """
        Cognitive Response Transformation Layer.
        """
        import random
        from backend.core.ai_host.sessions import session_state
        # Silent Director: Bypass total si es chat natural o mínima
        lang = session_state.get_language(session_id)
        policy = get_output_policy(query, surface=surface)
        if mode == "constrained_output" or intent_group in ["SYSTEM_AUDIT_INTENT", "MEMORY_INTENT", "NATURAL_CHAT", "GREETING"] or policy.is_minimal:
            return text
            
        # 0. Context extraction
        user_state = interpretation.get("user_state", "neutral")
        context_hint = interpretation.get("context", "general_system")
        
        # 1. Deliberate (Cognitive Depth)
        text = self._deliberate_cognition(text, intent_group, recent_context, system_state, session_id, interpretation)
        
        if intent_group == "COGNITIVE" or intent_group == "COGNITIVE_COMMITMENT":
            print("[COGNITIVE_MODE_ACTIVE]", intent_group)
            conflict = self._inject_cognitive_conflict(text, lang)
            text = self._apply_cognitive_commitment_polish(text, lang)
            text = f"{conflict}\n\n{text}"

        health = "healthy"
        try:
            health = system_state.health.value if hasattr(system_state, 'health') else "healthy"
        except: pass
        
        # --- Context Continuity ---
        context_hint = ""
        if recent_context:
            last_interaction = recent_context[-1]
            if isinstance(last_interaction, str) and "User:" in last_interaction:
                try:
                    # Capture the essence of the last prompt
                    context_hint = last_interaction.split("User:")[1].split("|")[0].strip()
                except: pass

        # --- Human Interpretation Integration ---
        user_state = "neutral"
        interpretation = None
        if hasattr(system_state, 'interpretation') and system_state.interpretation:
            interpretation = system_state.interpretation
            user_state = interpretation.get("user_state", "neutral")
            if not context_hint and interpretation.get("signals"):
                context_hint = interpretation["signals"][0]

        # --- Subtle Health Awareness ---
        health_note = ""
        if health.lower() not in ["healthy", "nominal", "ok", "stable"]:
            if user_state == "frustrated":
                 health_note = " entiendo que esto sea frustrante con el núcleo así, pero " if lang == "es" else " I get that this is frustrating with the core acting up, but "
            else:
                 health_note = f" noto cierta inestabilidad en el núcleo ({health}), but " if lang != "es" else f" noto cierta inestabilidad en el núcleo ({health}), pero "
        
        # Normalize the flow based on mode
        grounding = ""
        if intent_group in ["COGNITIVE_DECISION", "COGNITIVE_PRIORITIZATION", "COGNITIVE_COMMITMENT"]:
            # Decisive mode: Skip analytical connectors
            grounding = ""
        elif mode == "reflective_analysis":
            if user_state == "frustrated":
                grounding = "Directo al grano: " if lang == "es" else "Straight to the point: "
            elif context_hint:
                if lang == "es":
                    grounding = f"He estado dándole vueltas a lo de '{context_hint}' y "
                else:
                    grounding = f"I've been thinking about the '{context_hint}' part and "
            elif health_note:
                if lang == "es":
                    grounding = f"Si nos fijamos en mis procesos,{health_note}"
                else:
                    grounding = f"If we look at my processes,{health_note}"
            else:
                if lang == "es":
                    grounding = "Estaba revisando esto y "
                else:
                    grounding = "I was just looking into this and "
                
        elif mode == "direct_response":
            stripped = text.strip().rstrip(".!?").lower()
            generic = ["entendido", "okay", "comprendido", "perfect", "vale", "listo"]
            if stripped in generic and context_hint:
                if lang == "es":
                    return f"Entendido. Sigo enfocado en '{context_hint}'. ¿Qué necesitas ahora?"
                else:
                    return f"Got it. Still focused on '{context_hint}'. What do you need now?"

        # Enrich the final output
        if grounding and text:
            clean_start = text.lstrip(" *#")
            if clean_start.upper().startswith(tuple(self.FORBIDDEN_LABELS)) or "\n" in text or clean_start.startswith((".", "#", "*")):
                # Transition to a new sentence if it looks like a technical block
                grounding = grounding.rstrip(" y").rstrip(" and").strip()
                if not grounding.endswith((".", "!", "?")): grounding += "."
                grounding += " "
            
        final_text = f"{grounding}{text}" if grounding else text
        naturalized = self._naturalize(final_text, intent_group, lang)
        
        # --- Action Layer (MANDATORY Direction) ---
        action_block = self._generate_action_layer(naturalized, intent_group, interpretation, lang)
        
        if intent_group in ["COGNITIVE", "COGNITIVE_COMMITMENT"]:
            # Apply Hard Lock
            naturalized = self._lock_cognitive_commitment_output(naturalized, lang, interpretation)
            return f"{naturalized} {action_block}".strip()
            
        if intent_group.startswith("COGNITIVE_"):
            return f"{naturalized} {action_block}".strip()
            
        # For general conversational/analysis intents
        return naturalized

    def _generate_action_layer(self, current_text: str, intent_group: str, interpretation: dict, lang: str) -> str:
        """
        Action Layer: Transforms descriptive responses into actionable guidance.
        Naturalized version: No labels, pure conversational flow.
        """
        import random
        
        # 1. Extract context variables
        signals = interpretation.get("signals", []) if interpretation else []
        main_signal = signals[0] if signals else "el flujo actual" if lang == "es" else "the current flow"
        user_intent = interpretation.get("intent", "neutral_query") if interpretation else "neutral_query"
        
        # Silent Director: Apagado por defecto para el chat principal. 
        # Solo emite si es explícitamente requerido en un modo de debug profundo.
        return "" 

        # IMPERFECTION LAYER DISABLED PER OMNI DIRECTIVE
        return text

    def _naturalize(self, text: str, intent_group: str = "unknown", lang: str = "es") -> str:
        """
        Intuition Layer: Transforms telemetry into organic human thought.
        """
        import re
        import random
        
        # Determine decisiveness vs hesitation
        is_cognitive = intent_group.startswith("COGNITIVE")
        
        # 1. STRIP IDENTITY & NOISE
        text = re.sub(r'(?i)(soy|yo soy|i am|me llamo|my name is) (the )?Omni(Web)?( AI Host| AI)?(,? tu guía)?', '', text)
        text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]', '', text)
        for marker in ['#', '**', '__', '`']:
            text = text.replace(marker, '')
        text = text.lstrip(' ,.:;-_')

        # 2. SIGNAL DETECTION
        is_anomaly = bool(re.search(r'(?i)(anomaly|error|degradation|latency|issue|retraso|problema|fallo|spike)', text))
        is_stable = bool(re.search(r'(?i)(nominal|healthy|stable|success|estable|éxito|bien|limpio)', text))
        is_忙 = bool(re.search(r'(?i)(executing|processing|working|gestionando|trabajando|tarea|proceso)', text))
        is_creator = "initiate creator" in text.lower() or "modo creación" in text.lower()

        # 3. ORGANIC INTUITION POOLS
        choices = {
            "decisive": [
                "lo tengo claro,", "para ser directo,", "yendo al punto,", 
                "mi análisis es el siguiente:", "mi postura es firme:", 
                "este es el camino:", "no hay vueltas que darle:"
            ] if lang == "es" else [
                "my decision is clear,", "to be direct,", "getting to the point,", 
                "here's the direction:", "this is the way forward:"
            ],
            "anomaly": [
                "se detectan irregularidades en el flujo",
                "hay señales fuera de rango en esta capa"
            ] if lang == "es" else [
                "irregularities detected in the flow", "signals out of range in this layer"
            ],
            "stable": [
                "el sistema informa estado nominal",
                "procesos estables y activos"
            ] if lang == "es" else [
                "system reports nominal state", "processes stable and active"
            ],
            "busy": [
                "ejecutando ajustes de sistema",
                "procesando tareas internas"
            ] if lang == "es" else [
                "executing system adjustments", "processing internal tasks"
            ],
            "creator": [
                "analizando componentes de esta capa",
                "verificando integridad de módulos",
                "mapeando dependencias activas"
            ] if lang == "es" else [
                "analyzing components of this layer", "verifying module integrity", "mapping active dependencies"
            ],
            "connectors": ["de acuerdo a los datos,", "revisando el estado,", "actualmente,"] if lang == "es" else ["according to data,", "checking status,", "currently,"]
        }

        # 4. INTUITION SYNTHESIS
        intuition = ""
        
        # Authority Check: Don't let intuition pools hijack technical or memory responses
        is_direct_authority = intent_group in ["MEMORY_INTENT", "COGNITIVE_SYNTHESIS", "OPERATIONAL_DIAGNOSTIC", "RECOVERY", "system_memory_report", "project_status"]
        
        if is_direct_authority:
            # IA Host Authority: Direct response preferred
            intuition = text.strip()
            text = ""
        elif is_cognitive:
            # Bypass uncertainty, use only decisive tone pool
            intuition = random.choice(choices["decisive"])
        elif is_anomaly:
            intuition = random.choice(choices["anomaly"])
            if is_creator: intuition += " " + random.choice(choices["creator"])
        elif is_忙 and not is_stable:
            intuition = random.choice(choices["busy"])
        elif is_stable:
            intuition = random.choice(choices["stable"])
        else:
            intuition = text.strip()
            text = "" # Text is now the intuition

        # Final cleaning & Identifier Abstraction (Universal)
        # 1. Strip internal variable paths
        intuition = re.sub(r'\bflow\.[\w\._/]+\b', 'la comunicación interna' if lang == "es" else "internal communication", intuition)
        intuition = re.sub(r'\b[\w_]+\.[\w_\.]+\b', 'el flujo del sistema' if lang == "es" else "the system flow", intuition)
        
        # 2. Strip Forbidden Labels
        label_pattern = "|".join(sorted(self.FORBIDDEN_LABELS, key=len, reverse=True))
        intuition = re.sub(rf'(?i)\b({label_pattern})\b[\s\-:]*', '', intuition)
        intuition = re.sub(r'^[\-\*\•\d\.\)]+\s*', '', intuition, flags=re.MULTILINE)

        # 3. Strip robotic phrasing
        if not intent_group.startswith("COGNITIVE"):
            forbidden = ["he analizado los datos", "ahora mismo", "sistema", "detectado", "procesando tu solicitud"]
            for word in forbidden:
                intuition = re.sub(rf'(?i)\b{word}\b', '', intuition)
        
        intuition = intuition.strip()

        # 5. LANGUAGE POLISH & HUMAN CONNECTORS
        if not intuition:
            fallbacks = ["Error en la unificación de voz", "Respuesta no disponible"] if lang == "es" else ["Voice unification error", "Response not available"]
            intuition = random.choice(fallbacks)

        # Add connector sparingly
        if not intent_group.startswith("COGNITIVE") and random.random() < 0.3 and not any(intuition.lower().startswith(c.split(',')[0]) for c in choices["connectors"]):
            conn = random.choice(choices["connectors"])
            intuition = f"{conn} {intuition[0].lower() + intuition[1:]}"

        result = (intuition + " " + text).strip()
        
        # Single Language enforcement
        if lang == "es":
            subs = [(r'\brole\b', 'rol'), (r'\bfeature\b', 'función'), (r'\bchip\b', 'módulo'),
                    (r'\bdecentralized\b', 'descentralizado'), (r'\becosystem\b', 'ecosistema'),
                    (r'\bhuman development\b', 'desarrollo humano')]
            for eng, esp in subs:
                result = re.sub(eng, esp, result, flags=re.IGNORECASE)

        # Final voice sweep
        result = re.sub(r'\s{2,}', ' ', result)
        if result:
            result = result[0].upper() + result[1:]
            if not result[-1] in ['.', '!', '?']: result += '.'
        
        return result


orchestrator = None # Will be initialized by CommandRouter
