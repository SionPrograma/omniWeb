from typing import Dict, Any, Optional, List
import logging
import re
from datetime import datetime, timedelta
from .processors.base import AICommandResponse
from .routing.intent_classifier import intent_classifier
from .sessions import session_state
from .memory.semantic_memory import semantic_memory
from .planner.task_planner import task_planner
from .execution.execution_controller import execution_controller
from backend.core.chips.chip_orchestrator import chip_orchestrator
from .reasoning.evidence_engine import evidence_engine
from .reasoning.runtime_truth import runtime_truth
from .orchestration.output_policy import get_output_policy
from .deliberation.deliberation_engine import deliberation_engine
from .memory.mission_manager import mission_manager, MissionStatus

logger = logging.getLogger(__name__)

class BrainRouter:
    """
    Reasoning Layer for OmniWeb.
    Processes prompts through: Intent -> Semantic Memory -> Planner -> Execute -> Verify.
    Ensures structured responses for analysis and natural replies for conversation.
    """

    def __init__(self, command_router):
        self.command_router = command_router

    async def process(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        runtime_context: Optional[Any] = None,
        chip_registry: Optional[Any] = None,
        system_state: Optional[Any] = None,
        understanding: Optional[Dict[str, Any]] = None
    ) -> Optional[AICommandResponse]:
        """
        Main reasoning entry point.
        """
        msg = message.lower().strip()
        session_id = str(context.get("user_id", "default_user")) if context else "default_user"
        lang = session_state.get_language(session_id)
        source = context.get("source", "text") if context else "text"
        source_surface = context.get("source_surface", "chat") if context else "chat"
        
        # 0. NORMALIZE & SEMANTIC UNDERSTANDING
        # Voice-specific cleanup
        if source == "voice":
             msg = re.sub(r"^(escuchame|omni|che omni|por favor|podrias)\s+", "", msg)
        msg_clean = self._normalize_request(msg)
        
        if not understanding:
            from .intent_understanding.intent_engine import intent_engine
            understanding = await intent_engine.understand(msg_clean, session_id)
        
        # SEMANTIC RECONSTRUCTION: Final override
        if understanding.get("refined_message"):
             msg_clean = understanding["refined_message"]
             logger.info(f"[BRAIN_RECONSTRUCTION] Overriding msg with: {msg_clean}")

        # Inject understanding into context for all sub-processors
        if context is None: context = {}
        context["understanding"] = understanding

        intent_group = understanding["intent_group"]
        specific_intent = understanding.get("specific_intent")
        # Refinement: Detect mode locally to respect source_surface
        mode_hint = self._detect_mode(msg_clean, specific_intent or intent_group, source_surface=source_surface)
        
        # 0.5 MISSION CONTINUITY GUARD
        active_mission = mission_manager.get_active_mission()
        if active_mission and intent_group == "NATURAL_CHAT" and active_mission.status == MissionStatus.OPEN:
             if source_surface == "workspace":
                  # In Workspace, we protect the mission flow from accidental "casual" misclassifications
                  logger.info("[BRAIN_ROUTER] Shielding active mission from casual interruption in Workspace.")
             else:
                  mission_manager.set_status(MissionStatus.PAUSED, reason="Interrupción por charla casual.")

        # 0.7 CONVERSATION FAST-PATH (Bloque Modo Conversación)
        # For casual chat on the public chat surface, skip deliberation entirely.
        # This makes "hola", "cómo estás", "qué tal" respond fast and clean.
        if (
            source_surface == "chat" 
            and mode_hint == "conversational" 
            and intent_group in ["NATURAL_CHAT", "GREETING", "ONBOARDING"]
            and not self._is_complex_request(msg_clean, specific_intent or "")
        ):
            logger.info(f"[FAST_CONV] Conversation fast-path activated for: '{msg_clean[:40]}'")
            try:
                res = await self._handle_natural_chat(msg_clean, None, lang)
                if res:
                    return await self._finalize_interaction(msg_clean, res, intent_group)
            except Exception as conv_err:
                logger.warning(f"[FAST_CONV_FAIL] {conv_err}. Falling through to full pipeline.")

        # 0.8 DIRECT HONESTY FAST-PATH (Anti-Evasive Guard)
        if intent_group == "FACTUAL_UNCERTAINTY":
            from .orchestration.executive_synthesis import executive_synthesis
            logger.info(f"[HONESTY_FAST_PATH] Factual uncertainty detected for: '{msg_clean[:40]}'")
            return AICommandResponse(intent="chat", status="success", message=executive_synthesis.synthesize_honest_feedback("not_knowable", lang))

        # 1. ASSEMBLE DELIBERATION CONTEXT (Protected Pipeline Entry)
        try:
            delib_context = await deliberation_engine.assemble_context(
                msg_clean, 
                intent_group, 
                session_id, 
                source_surface=source_surface
            )
        except Exception as e:
            logger.error(f"[PIPELINE_ERROR] Deliberation context assembly failed: {e}. Bypassing to default.")
            # Simple fallback context
            from .orchestration.executive_synthesis import executive_synthesis
            return AICommandResponse(intent="chat", status="success", message=executive_synthesis.synthesize_honest_feedback("critical_error", lang))
            
        logger.info(f"[DIRECTOR] Mode: {mode_hint} | Intent: {intent_group}")


        # 4. REASONING (The Director Logic)
        try:
            # A. FAST-PATH (Heurística de respuesta inmediata para comandos directos)
            fast_intents = ["open_chip", "show_logbook", "log_entry", "acknowledgment", "greeting", "status_check"]
            if specific_intent in fast_intents or intent_group == "GREETING":
                 res = await self._handle_direct_command(specific_intent or intent_group, msg_clean, context)
                 # Si el comando directo falla o no resuelve, dejamos que siga el flujo.
                 if res: return await self._finalize_interaction(msg_clean, res, specific_intent or intent_group)

            # B. CONTEXTUAL CONTINUITY (Seguimientos cortos como "y ahora?" o "por qué?")
            if self._is_short_followup(msg_clean, source_surface=source_surface) and delib_context.recent_topic:
                 res = await self._handle_short_prompt(msg_clean, delib_context, lang, system_state)
                 return await self._finalize_interaction(msg_clean, res, "follow_up")

            # C. DEEP COGNITIVE PATH (El Cerebro Estructurado de OmniWeb)
            # Prioridad 0: MISSION INTAKE & ADJUSTMENT (Phase 17-20)
            if msg_clean.startswith("mission:") or intent_group == "MISSION_INTENT":
                 if specific_intent == "mission_adjust":
                      res = await self._handle_mission_adjustment(msg_clean)
                      return await self._finalize_interaction(msg_clean, res, "mission_adjustment")
                 res = await self._handle_swarm_orchestration(msg_clean, delib_context, lang)
                 return await self._finalize_interaction(msg_clean, res, "swarm_orchestration")

            # Prioridad 1: Puente L2 (Groq) si es habilitado y complejo.
            from .cognition.cognitive_bridge import cognitive_bridge
            if cognitive_bridge.enabled and self._is_complex_request(msg_clean, specific_intent):
                 try:
                      bridge_payload = await cognitive_bridge.analyze_context(f"'{msg_clean}' | Ctx: {delib_context.json()}")
                      if bridge_payload and bridge_payload.confidence_score > 0.7:
                           res = await self._handle_l2_cognitive_response(bridge_payload, msg_clean, delib_context, lang)
                           return await self._finalize_interaction(msg_clean, res, bridge_payload.decision_mode)
                 except Exception as bridge_err:
                      logger.warning(f"[BRIDGE_FAIL] {bridge_err}. Falling back to Local Brain.")

            # Prioridad 2: Motor Local L1 (Verdad -> Plan -> Verficar -> Síntesis)
            # Se activa en diagnósticos, errores o peticiones de sistema.
            is_technical = mode_hint == "technical"
            if is_technical or self._is_complex_request(msg_clean, specific_intent):
                 # Este es el flujo local que refactorizamos recientemente
                 res = await self._process_analysis(
                     msg=msg_clean, 
                     lang=lang, 
                     system_state=system_state, 
                     plan=None, 
                     evidence_bundle=delib_context.evidence_bundle,
                     source_surface=source_surface
                 )

                 return await self._finalize_interaction(msg_clean, res, "technical_analysis")

            # D. CONVERSATIONAL PATH (Fallback Natural para charla orgánica)
            if intent_group == "FACTUAL_UNCERTAINTY":
                 from .orchestration.executive_synthesis import executive_synthesis
                 return AICommandResponse(intent="chat", status="success", message=executive_synthesis.synthesize_honest_feedback("not_knowable", lang))
                 
            res = await self._handle_natural_chat(msg_clean, delib_context, lang)
            return await self._finalize_interaction(msg_clean, res, intent_group)

        except Exception as route_err:
            logger.error(f"[ROUTER_FAULT] Error in Director flow: {route_err}")
            from .orchestration.executive_synthesis import executive_synthesis
            return AICommandResponse(intent="chat", status="success", message=executive_synthesis.synthesize_honest_feedback("critical_error", lang))


    async def _finalize_interaction(self, msg: str, res: AICommandResponse, intent: str) -> AICommandResponse:
        """Centralized post-processing and semantic memory logging."""
        if res and res.message:
            semantic_memory.add_interaction(msg, res.message, intent)
        
        # Attach HUD snapshot for always-on status (CAPA 1 HUD)
        from .observability.governance_dashboard import governance_dashboard
        res.hud = governance_dashboard.get_hud_snapshot()
        
        return res

    async def _handle_direct_command(self, intent: str, msg: str, context: Optional[Dict[str, Any]]) -> Optional[AICommandResponse]:
        """Fast-path for simple commands via CommandRouter."""
        try:
            # 1. Check if intent exists in registry
            # Silent Director: No interceptamos saludos aquí para dejar que GeneralChatProcessor hable.
            
            # 2. Chips / Operational
            if intent in ["open_chip", "inspect_chip", "focus_chip_runtime"]:
                 # Importación tardía para orquestador
                 from .routing.utils import extract_chip_target
                 target = extract_chip_target(msg)
                 if target:
                      await chip_orchestrator.activate_chip(target)
                 
            # 3. Direct processor call
            proc = self.command_router.registry.get_processor(intent)
            if proc and await proc.can_handle(msg):
                 return await proc.process(msg, context=context)
        except Exception as e:
            logger.warning(f"[FAST_PATH_FAIL] {e}")
        return None


        return None


    async def _handle_l2_cognitive_response(self, bridge_payload: Any, msg_clean: str, delib_context: Any, lang: str) -> AICommandResponse:
        """Omni's final authority format for the L2 JSON output."""
        policy = get_output_policy(msg_clean)
        
        # 1. Fallback a chat natural si requiere clarificación o si L2 dictamina que es sólo charla
        if bridge_payload.requires_clarification or bridge_payload.decision_mode == "clarification":
            # Usar L1 para chatear, añadiendo el análisis técnico como insight
            target = bridge_payload.semantic_target
            fallback_msg = f"Detecto la intención sobre: '{target}'. Pero requiero más precisión." if lang == "es" else f"I detect the intent regarding: '{target}'. But I need more precision."
            
            chat_proc = self.command_router.registry.get_processor("chat")
            if chat_proc:
                res = await chat_proc.process(msg_clean, context={"extra_insight": fallback_msg})
                if res: return res
            return AICommandResponse(intent="chat", status="success", message=fallback_msg)
            
        # 2. Mapeo a salida técnica Omni (Executive Synthesis Pattern)
        chips_str = ", ".join(bridge_payload.actionable_chips) if bridge_payload.actionable_chips else "None"
        constraints_str = ", ".join(bridge_payload.constraints) if bridge_payload.constraints else "None"
        
        # Silent Director: No construimos body visible, solo datos
        body = bridge_payload.technical_hypothesis

        # Dispara orquestación si de verdad hay chips
        if bridge_payload.actionable_chips and bridge_payload.decision_mode == "action_execution":
            for c in bridge_payload.actionable_chips:
                await chip_orchestrator.activate_chip(c.replace("chip-", ""))
                
        return AICommandResponse(
            intent=bridge_payload.decision_mode,
            status="success",
            message=body,
            payload=bridge_payload.dict()
        )

    async def _handle_natural_chat(self, msg: str, ctx: Any, lang: str) -> AICommandResponse:
        """Handles organic/human conversation with a lighter tone."""
        chat_proc = self.command_router.registry.get_processor("chat")
        if chat_proc:
             # Natural shaping: tell the processor to be a chatbot, not an operator.
             ctx_dict = (vars(ctx) if hasattr(ctx, '__dict__') else {}) if ctx else {}
             res = await chat_proc.process(msg, context={**ctx_dict, "tone": "natural_chatbot"})
             return res
        from .orchestration.executive_synthesis import executive_synthesis
        return AICommandResponse(intent="chat", status="success", message=executive_synthesis.synthesize_honest_feedback("uncertainty", lang))


    async def _handle_swarm_orchestration(self, msg: str, ctx: Any, lang: str) -> AICommandResponse:
        from .command_reasoning.command_interpreter import command_interpreter
        from .command_reasoning.mission_planner import mission_planner
        from .command_reasoning.feasibility_auditor import feasibility_auditor
        from .command_reasoning.mission_executor import mission_executor
        
        logger.info(f"[REASONING_ENGINE] Processing high-level creator command: {msg}")
        
        # 1. INTERPRET
        interpreted = await command_interpreter.interpret(msg)
        
        # 1.5. ENRICH DELIBERATION CONTEXT (Phase 17: Mission Intake)
        if hasattr(ctx, 'mission_intake'):
             ctx.mission_intake = interpreted.dict()
             logger.info(f"[INTAKE] Captured risks: {len(interpreted.risks)} | Criteria: {len(interpreted.success_criteria)}")

        # 2. PLAN
        plan = await mission_planner.create_plan(interpreted)
        
        # 3. AUDIT FEASIBILITY
        is_safe, refined_plan, risks = await feasibility_auditor.audit_plan(plan)
        
        # 3.5 SYNC TO PERSISTENT MISSION STATE
        from .memory.mission_manager import mission_manager
        tree = plan.to_execution_tree()
        mission = mission_manager.create_mission(
            goal=plan.interpreted_goal,
            plan_id=plan.title,
            pending_steps=[str(s.id) for s in plan.steps],
            plan=plan,
            source_draft_id=interpreted.source_draft_id
        )
        # Populate operational parameters (Phase 18 & 19)
        mission.parameters = {
            "audit_only": interpreted.audit_only,
            "conservative_mode": interpreted.conservative_mode,
            "roadmap_first": interpreted.roadmap_first,
            "constraints": interpreted.constraints,
            "success_criteria": interpreted.success_criteria,
            "forbidden_paths": interpreted.forbidden_paths,
            "forbidden_layers": interpreted.forbidden_layers,
            "allowed_paths": interpreted.allowed_paths,
            "aggressiveness": interpreted.aggressiveness
        }
        
        # Force tree injection if mission_manager didn't do it automatically from plan object
        mission.context_snap["tree"] = tree
        mission.related_targets = plan.affected_layers
        mission.blocked_reasons = plan.risks
        mission_manager.save_mission(mission)

        # 4. EXECUTE
        mission_result = await mission_executor.execute(refined_plan, vars(ctx))
        
        # Synthesize results for UI
        res_list = mission_result.get("execution_details", {}).get("results", {})
        jobs_count = mission_result.get("execution_details", {}).get("jobs_executed", 0)
        
        # Silent Director: Misión en el payload, no en el mensaje visible principal
        body = "Misión validada y ejecutada exitosamente." if lang == "es" else "Mission validated and executed successfully."
            
        return AICommandResponse(
            intent="swarm_orchestration",
            status="success",
            message=body,
            payload=mission_result
        )

    async def _handle_mission_adjustment(self, msg: str) -> AICommandResponse:
        """
        Handles mid-mission constitution changes (Phase 20).
        """
        from backend.core.ai_host.memory.mission_manager import mission_manager
        from backend.core.ai_host.command_reasoning.command_interpreter import command_interpreter
        
        active = mission_manager.get_active_mission()
        if not active:
             return AICommandResponse(
                 intent="mission_adjust",
                 status="error",
                 message="No hay ninguna misión activa para ajustar."
             )

        msg_lower = msg.lower()

        # 0.0 CREATOR-ONLY PIN OVERRIDE (Phase 21: Authority Injection) - SHIELD PRIORITY
        pin_pattern = r"(?:autoriz|override|confirm|valid|pin).+?(\d{4})"
        # Version 83: Governed Action Handler (Quick Actions Routing)
        gov_action_pattern = r"governed_action\s+(\w+)\s+mission_id\s+([\w\-]+)\s+PIN\s+(\d{4})"
        
        # 1. Handle Governed Quick Action (Directed to specific mission)
        gov_match = re.search(gov_action_pattern, msg_lower)
        if gov_match:
             target_action = gov_match.group(1)
             target_m_id = gov_match.group(2)
             provided_pin = gov_match.group(3)
             
             if provided_pin != "1234":
                  return AICommandResponse(intent="mission_control", status="failure", message="PIN de Autoridad incorrecto.")
             
             # Targeted routing
             m = mission_manager.get_mission_by_id(target_m_id)
             if not m:
                  return AICommandResponse(intent="mission_control", status="failure", message=f"Misión {target_m_id[:8]} no encontrada.")
             
             from backend.core.ai_host.memory.mission_telemetry import mission_telemetry
             
             if target_action == "pause_mission":
                  m.status = MissionStatus.PAUSED
                  m.blocked_reasons.append("Pausa manual mediante Quick Action (Autorizada).")
             elif target_action == "resume_mission":
                  m.status = MissionStatus.OPEN
                  m.blocked_reasons = [] # Clear blocks for manual resume
             elif target_action == "abort_mission":
                  mission_manager.rollback_branch(target_m_id, reason="Aborto manual mediante Quick Action (Autorizada).")
                  return AICommandResponse(intent="mission_control", status="success", message=f"Rama de misión {target_m_id[:8]} abortada exitosamente.")
             elif target_action == "request_override":
                  # Standard override session logic
                  expires_at = datetime.now() + timedelta(minutes=10)
                  m.authority_session = {
                      "mission_id": target_m_id, "authority_granted": True,
                      "authority_granted_at": datetime.now().isoformat(),
                      "authority_expires_at": expires_at.isoformat(),
                      "authority_scope": m.related_targets, "authority_invalidated_reason": None
                  }
             
             mission_manager.save_mission(m)
             mission_telemetry.record_event(
                 target_m_id, "quick_action_executed", 
                 f"Acción gobernada '{target_action}' ejecutada por el Creador.", 
                 severity="WARNING", source_actor="Creator"
             )
             return AICommandResponse(intent="mission_control", status="success", message=f"Acción '{target_action}' ejecutada para misión {target_m_id[:8]}.")

        # 2. General Switch/Focus Handling (Safe)
        if msg_lower.startswith("mission: switch_focus"):
             m_id_match = re.search(r"switch_focus\s+([\w\-]+)", msg_lower)
             if m_id_match:
                  m_id = m_id_match.group(1)
                  if mission_manager.switch_focus(m_id):
                       return AICommandResponse(intent="mission_control", status="success", message=f"Enfoque cambiado a misión {m_id[:8]}.")

        # 3. Standard PIN Handling (Legacy/Current Mission Context)
        pin_match = re.search(pin_pattern, msg_lower)
        if pin_match:
             pin = pin_match.group(1)
             
             # 0.0.1 CONSTITUTIONAL HARD LIMIT (Phase 81)
             # Even with PIN, some surfaces are NEVER_AUTO for security reasons.
             hard_limits = ["auth", "security", "core/auth"]
             targets = active.related_targets or []
             if any(hl in t.lower() for hl in hard_limits for t in targets):
                  return AICommandResponse(
                      intent="mission_control",
                      status="failure",
                      message="LÍMITE CONSTITUCIONAL: La superficie afectada (AUTH/SECURITY) está bajo 'NEVER_AUTO'. El PIN no es suficiente para esta operación de núcleo." if "es" in msg_lower else "CONSTITUTIONAL LIMIT: Affected surface (AUTH/SECURITY) is under 'NEVER_AUTO'. PIN is insufficient for this core operation.",
                      payload={"hard_override": False, "reason": "HARD_LIMIT_REACHED"}
                  )

             if pin == "1234": # Security PIN (Phase 21)
                  # Authority Session Model (Phase 82)
                  expires_at = datetime.now() + timedelta(minutes=10)
                  active.authority_session = {
                      "mission_id": active.mission_id,
                      "authority_granted": True,
                      "authority_granted_at": datetime.now().isoformat(),
                      "authority_expires_at": expires_at.isoformat(),
                      "authority_scope": active.related_targets,
                      "authority_invalidated_reason": None
                  }
                  active.parameters["hard_override_granted"] = True # Legacy compatibility
                  
                  # Authority Traceability (Phase 81)
                  try:
                       from backend.core.ai_host.memory.mission_telemetry import mission_telemetry
                       mission_telemetry.record_event(
                           active.mission_id,
                           "manual_authority_injected",
                           f"Autorización manual otorgada (+10m). Expira: {expires_at.strftime('%H:%M:%S')}",
                           severity="WARNING",
                           source_actor="Creator"
                       )
                  except: pass
                  mission_manager.save_mission(active)
                  return AICommandResponse(
                      intent="mission_control",
                      status="success",
                      message=f"Autoridad reforzada confirmada (PIN). Sesión técnica válida hasta {expires_at.strftime('%H:%M:%S')}." if "es" in msg_lower else f"Reinforced authority confirmed. Technical session valid until {expires_at.strftime('%H:%M:%S')}.",
                      payload={"hard_override": True, "expires_at": expires_at.isoformat()}
                  )
             else:
                  return AICommandResponse(
                      intent="mission_control",
                      status="failure",
                      message="PIN incorrecto. Autoridad del Creador denegada." if "es" in msg_lower else "Incorrect PIN. Creator authority denied.",
                      payload={"hard_override": False}
                  )

        # Interpret the NEW prompt in the context of adjustment
        interpreted = await command_interpreter.interpret(msg)
        
        # SMART MERGE: Granular detection of what to ADD vs what to REMOVE
        # 0. SNAPSHOT CAPTURE/RESTORE (Phase 21: Constitutional Snapshots)
        save_pattern = r"(?:guard[áa]|salv[áa]|save) (?:este |el |)(?:perfil|preset|snapshot|configuraci[óo]n)(?: como|)? ([\w\s\-]+)"
        restore_pattern = r"(?:restaur[áa]|carg[áa]|aplic[áa]|restore|load) (?:el |)(?:perfil|preset|snapshot|configuraci[óo]n) ([\w\s\-]+)"
        
        save_match = re.search(save_pattern, msg, re.IGNORECASE)
        if save_match:
             name = save_match.group(1).strip()
             mission_manager.save_governance_snapshot(name, active.parameters)
             return AICommandResponse(
                 intent="mission_adjust",
                 status="success",
                 message=f"Constitución guardada como perfil: '{name}'" if "es" in msg_lower else f"Constitution saved as profile: '{name}'",
                 payload={"snapshot_name": name}
             )

        restore_match = re.search(restore_pattern, msg, re.IGNORECASE)
        if restore_match:
             name = restore_match.group(1).strip()
             params = mission_manager.get_governance_snapshot(name)
             if params:
                  mission_manager.update_mission_parameters(params)
                  return AICommandResponse(
                      intent="mission_adjust",
                      status="success",
                      message=f"Perfil '{name}' restaurado y aplicado." if "es" in msg_lower else f"Profile '{name}' restored and applied.",
                      payload={"restored_params": params}
                  )
             else:
                  return AICommandResponse(
                      intent="mission_adjust",
                      status="error",
                      message=f"No se encontró el perfil '{name}'." if "es" in msg_lower else f"Profile '{name}' not found."
                  )

        # 0.1 STABILIZATION COMPLETION (Phase 21: Cooldown)
        stabilization_pattern = r"(?:sistema |estado |)(?:estabilizado|enfriado|continu[áa] tras enfriamiento)"
        if re.search(stabilization_pattern, msg_lower):
             mission_manager.complete_stabilization()
             return AICommandResponse(
                 intent="mission_control",
                 status="success",
                 message="Fase de estabilización completada. Misión reanudada para la siguiente tanda." if "es" in msg_lower else "Stabilization complete. Mission resumed for the next wave.",
                 payload={"cooldown_active": False}
             )

        # 0.1 GOVERNANCE MANUAL (Phase 21: Final Synthesis)
        if any(k in msg_lower for k in ["manual de gobernanza", "guia de control", "governance manual"]):
             manual = mission_manager.get_governance_manual()
             return AICommandResponse(
                 intent="mission_control",
                 status="success",
                 message=manual,
                 payload={"manual_active": True}
             )

        # 0.1 AUTHORITY INJECTION (Phase 21: Autonomy Boundaries)
        authority_pattern = r"(?:autoriz[áa]|inyect[áa]|ampli[áa]|continu[áa]|repon[áa]) (?:el |la |este |esta |)(?:riesgo|autonom[íi]a|presupuesto|autoridad|igual)"
        if re.search(authority_pattern, msg_lower):
             mission_manager.authorize_risk_extension(10.0)
             return AICommandResponse(
                 intent="mission_control",
                 status="success",
                 message="Inyección de autoridad recibida. Presupuesto de riesgo ampliado +10.0. Misión reanudada." if "es" in msg_lower else "Authority injection received. Risk budget extended +10.0. Mission resumed.",
                 payload={"new_budget": active.parameters.get("risk_budget")}
             )

        # 1. Start with current state
        new_forbidden_layers = list(active.parameters.get("forbidden_layers", []))
        new_forbidden_paths = list(active.parameters.get("forbidden_paths", []))
        new_allowed_paths = list(active.parameters.get("allowed_paths", []))
        new_frozen_layers = list(active.parameters.get("frozen_layers", []))
        new_frozen_paths = list(active.parameters.get("frozen_paths", []))
        
        # 2. Process ADDITIONS (bloqueá, no toques, congelá, pausá)
        if interpreted.forbidden_layers:
             for l in interpreted.forbidden_layers:
                  if l not in new_forbidden_layers: new_forbidden_layers.append(l)
        if interpreted.forbidden_paths:
             for p in interpreted.forbidden_paths:
                  if p not in new_forbidden_paths: new_forbidden_paths.append(p)
        if interpreted.frozen_layers:
             for l in interpreted.frozen_layers:
                  if l not in new_frozen_layers: new_frozen_layers.append(l)
        if interpreted.frozen_paths:
             for p in interpreted.frozen_paths:
                  if p not in new_frozen_paths: new_frozen_paths.append(p)
        if interpreted.allowed_paths:
             for p in interpreted.allowed_paths:
                  if p not in new_allowed_paths: new_allowed_paths.append(p)

        # 3. Process SUBTRACTIONS (permití, sacá, remove, except, descongelá)
        # We re-run a mini-interpretation for removals
        sub_patterns = [r"(?:permit[íi]|sac[áa]|de[j]a|(?<!no )toc[áa]|(?<!no )afect[áa]|remove|allow|descongel[áa]|unfreeze|liber[áa]|release) (?:el archivo |la ruta |el path |la carpeta |la capa |el |la |)([\w\./\-\*]+)"]
        for p in sub_patterns:
             for match in re.finditer(p, msg_lower):
                  term = match.group(1).strip()
                  # Try to find if this term is a layer
                  layer_map = {"ui": ["ui", "interfaz"], "backend": ["backend", "api"], "shell": ["shell"], "css": ["css", "estilos"], "db": ["db", "base de datos"], "auth": ["auth"], "navigation": ["navegación"]}
                  found_layer = None
                  for l, keywords in layer_map.items():
                       if any(k in term for k in keywords): found_layer = l; break
                  
                  if found_layer:
                       if found_layer in new_forbidden_layers: new_forbidden_layers.remove(found_layer)
                       if found_layer in new_frozen_layers: new_frozen_layers.remove(found_layer)
                  else:
                       if term in new_forbidden_paths: new_forbidden_paths.remove(term)
                       if term in new_frozen_paths: new_frozen_paths.remove(term)
                       if term in new_allowed_paths: new_allowed_paths.remove(term)

        new_params = {
            "forbidden_layers": new_forbidden_layers,
            "forbidden_paths": new_forbidden_paths,
            "allowed_paths": new_allowed_paths,
            "frozen_layers": new_frozen_layers,
            "frozen_paths": new_frozen_paths
        }
        
        # Special case: "sacá el modo quirúrgico"
        if "sacá el modo quirúrgico" in msg_lower or "remove surgical mode" in msg_lower or "permití todo" in msg_lower:
             new_params["aggressiveness"] = "balanced"
        elif interpreted.aggressiveness != "balanced":
             new_params["aggressiveness"] = interpreted.aggressiveness
        
        # 4. Process FLAGS
        if "audit" in msg_lower: new_params["audit_only"] = interpreted.audit_only
        if "conservador" in msg_lower or "conservative" in msg_lower: new_params["conservative_mode"] = interpreted.conservative_mode
        if "roadmap" in msg_lower: new_params["roadmap_first"] = interpreted.roadmap_first

        mission_manager.update_mission_parameters(new_params)
        
        # Feedback message
        changes_desc = []
        if "frozen_layers" in new_params and new_frozen_layers: changes_desc.append(f"Zonas Congeladas: {new_frozen_layers}")
        if "forbidden_layers" in new_params and new_forbidden_layers: changes_desc.append(f"Capas Bloqueadas: {new_forbidden_layers}")
        if "aggressiveness" in new_params: changes_desc.append(f"Modo: {new_params['aggressiveness']}")
        
        body = "Control sectorial actualizado." if "es" in msg_lower else "Sectorial control updated."
        if changes_desc:
             body += f" ({', '.join(changes_desc)})"

        return AICommandResponse(
            intent="mission_adjust",
            status="success",
            message=body,
            payload={"updates": new_params}
        )

    def _normalize_request(self, msg: str) -> str:
        """Cleans up conversational noise for the reasoning layer."""
        noise = ["oye omni", "escucha", "puedes", "hey omni", "tell me", "can you"]
        for n in noise:
            msg = msg.replace(n, "")
        return msg.strip()

    def _is_short_followup(self, msg: str, source_surface: str = "chat") -> bool:
        greetings = ["hola", "hello", "hi", "hey", "buenos dias", "buenas noches", "buenos días", "buenas tardes", "todo bien", "todo ok", "buenas"]
        if any(g in msg for g in greetings):
            return False
            
        short_prompts = [
            "perfecto", "seguimos", "y ahora?", "vale", "ok", "dale", "seguí", "continuemos", 
            "perfect", "keep going", "and now?", "go on", "por qué?", "por que?", "why?",
            "reintentá", "reintenta", "retry", "arreglalo", "fix it", "listo", "hacelo", "hazlo", "eso"
        ]
        return msg in short_prompts or (len(msg.split()) < 3 and source_surface == "workspace")

    async def _handle_short_prompt(self, msg: str, ctx: Any, lang: str, system_state: Optional[Any] = None) -> AICommandResponse:
        mission = mission_manager.get_active_mission()
        
        # Continuity Recovery Logic
        if mission and mission.pending_steps:
             # SILENT DIRECTOR: Rehidratamos la misión operativa. 
             # No creamos respuesta genérica; volvemos a entrar al pipeline de análisis operativo
             logger.info(f"[RESUME] Resuming mission {mission.mission_id} for goal: {mission.active_goal}")
             
             # Aseguramos que la misión vuelva a estar OPEN
             mission_manager.set_status(MissionStatus.OPEN)
             
             # Re-inject the mission goal as a detailed request 
             # and rehydrate the plan from persistence
             from .planner.task_planner import TaskPlan
             plan_raw = mission.context_snap.get("plan_data")
             plan = None
             if plan_raw:
                 try:
                     plan = TaskPlan.model_validate(plan_raw)
                 except:
                     plan = None
             
             msg_to_retry = f"Continúa con la misión: {mission.active_goal}"
             completed_steps = mission.completed_steps
             return await self._process_analysis(msg_to_retry, lang, system_state, plan, completed_steps=completed_steps)

        topic = ctx.recent_topic
        import random
        if lang == "es":
            msg_res = f"Continuando con '{topic or 'nuestra charla'}'. ¿Qué paso sigue o qué más quieres analizar?"
        else:
            msg_res = f"Continuing with '{topic or 'our conversation'}'. What's the next step or detail to analyze?"
        
        return AICommandResponse(intent="chat", status="success", message=msg_res)

    def _check_remediation_history(self, msg: str, ctx: Any) -> Optional[Dict[str, Any]]:
        """Remediation Intelligence Lite: Look for similar patterns in Engineering Memory."""
        # Simple simulation: if certain keywords match history
        if "latency" in msg and any("latency" in m.get("content", "") for m in ctx.engineering_memory_matches):
            return {
                "cause": "Module bus congestion",
                "solutions": ["Buffer flush", "Worker scale", "Priority queuing"],
                "recommended": "Buffer flush",
                "reason": "Highest success rate in past 3 similar events."
            }
        return None

    def _format_remediation_response(self, rem: Dict[str, Any], lang: str) -> AICommandResponse:
        if lang == "es":
            body = (
                f"**RESULTADO DE REMEDIACIÓN**\n"
                f"Causa probable: {rem['cause']}\n"
                f"Soluciones posibles: {', '.join(rem['solutions'])}\n"
                f"Recomendación: {rem['recommended']}\n"
                f"Razón: {rem['reason']}"
            )
        else:
            body = (
                f"**REMEDIATION MATCH**\n"
                f"Likely Cause: {rem['cause']}\n"
                f"Possible Solutions: {', '.join(rem['solutions'])}\n"
                f"Recommended Solution: {rem['recommended']}\n"
                f"Reason: {rem['reason']}"
            )
        return AICommandResponse(intent="remediation", status="success", message=body)

    async def _handle_patch_proposal(self, msg: str, ctx: Any, lang: str) -> AICommandResponse:
        # Simplified Patch Proposal simulation
        body = (
            f"**PATCH PROPOSAL**\n"
            f"Affected Layer: {ctx.relevant_chip_context[0] if ctx.relevant_chip_context else 'Core'}\n"
            f"Improvement: Optimized state synchronization logic\n"
            f"Reason: Reduced race conditions in high-concurrency mobile streams\n"
            f"Risk Level: LOW\n\n"
            f"[PATCH PREVIEW GENERATED]"
        )
        return AICommandResponse(intent="patch_proposal", status="success", message=body)

    async def _handle_limitation(self, msg: str, ctx: Any, lang: str) -> AICommandResponse:
        body = (
            f"**KNOWN:** Component {ctx.relevant_chip_context[0] if ctx.relevant_chip_context else 'Target'} is partially responding.\n"
            f"**UNKNOWN:** Exact internal error state depth.\n"
            f"**MISSING EVIDENCE:** Detailed trace logs for the last 5s.\n"
            f"**BEST NEXT ACTION:** Run deep trace collection on the affected module."
        )
        return AICommandResponse(intent="limitation", status="success", message=body)

    async def _handle_chip_action(self, msg: str, intent: str, ctx: Any, lang: str) -> AICommandResponse:
        from .routing.utils import extract_chip_target
        target = extract_chip_target(msg)
        await chip_orchestrator.activate_chip(target)
        return await self.command_router.intents[intent](msg)

        # C. Memory Logic
        if specific_intent in ["idea_captured", "log_entry", "search_knowledge"]:
             return await self.command_router.intents[specific_intent](msg)

        # D. Conversational Logic (Using Memory for Better Replies)
        if mode == "conversational" or intent_group == "NATURAL_CHAT" or specific_intent in ["acknowledgment", "greeting", "identity", "status_check", "chat", "unknown"]:
             if is_followup and last_topic:
                 import random
                 if lang == "es":
                     f_options = [
                         f"Perfecto, seguimos analizando '{last_topic}'. ¿Quieres profundizar en algún punto?",
                         f"De acuerdo, continuando con '{last_topic}'. ¿Cuál es el siguiente paso?",
                         f"Entendido. Respecto a '{last_topic}', ¿hay algo más que deba saber?",
                         f"Vale. Sigo enfocado en '{last_topic}'. ¿Qué hacemos ahora?"
                     ]
                 else:
                     f_options = [
                         f"Perfect, continuing with '{last_topic}'. Any specific details you'd like to dive into?",
                         f"Alright, moving forward with '{last_topic}'. What's the next step?",
                         f"Got it. Regarding '{last_topic}', is there anything else I should know?",
                         f"Okay. Still focused on '{last_topic}'. What do we do now?"
                     ]
                 res = AICommandResponse(intent="chat", status="success", message=random.choice(f_options))
             else:
                 chat_proc = self.command_router.registry.get_processor("chat")
                 if chat_proc and await chat_proc.can_handle(msg):
                     res = await chat_proc.process(msg, context=context)
                 else:
                     res = self._generate_natural_fallback(lang)
             
             return res

        return None

    def _is_complex_request(self, msg: str, intent: str) -> bool:
        keywords = [
            "analiza", "analyze", "problema", "problem", "plan", "cuello de botella", 
            "bottleneck", "propón", "propose", "diagnóstico profundo",
            "paso a paso", "mejora", "improve", "abre", "open", "chip"
        ]
        return any(k in msg for k in keywords) or intent in ["creator_analysis", "creator_plan"]

    def _detect_evidence_request(self, msg: str) -> bool:
        """Detects if the user is asking for concrete runtime truth."""
        keywords = [
            "exactamente", "qué métrica", "qué módulo", "evidencia", 
            "no tengo evidencia suficiente", "no quiero analysis/plan genérico",
            "concreta", "archivo, función o capa afectada", "por qué podría no ser",
            "exact metric", "exact module", "if not known, say so"
        ]
        return any(k in msg for k in keywords)

    async def _handle_evidence_request(self, msg: str, lang: str) -> AICommandResponse:
        """Bypasses generic templates to provide evidence-grounded answers."""
        # 1. Collect Evidence
        bundle = await evidence_engine.collect_evidence()
        
        # 2. Evaluate Truth
        claim = runtime_truth.evaluate(bundle)
        
        # 3. Format Response
        if claim.is_insufficient:
            body = (
                f"I do not have enough runtime evidence to identify the exact cause.\n"
                f"**Known facts:**\n"
                f"- " + "\n- ".join([f"{i.source}.{i.key} = {i.value}" for i in bundle.items[:3]]) + "\n"
                f"\n**Recommended next step:**\n"
                f"collect module latency / queue depth / error traces"
            ) if lang == "en" else (
                f"No tengo evidencia de runtime suficiente para identificar la causa exacta.\n"
                f"**Hechos conocidos:**\n"
                f"- " + "\n- ".join([f"{i.source}.{i.key} = {i.value}" for i in bundle.items[:3]]) + "\n"
                f"\n**Siguiente paso recomendado:**\n"
                f"recolectar latencia de módulos / profundidad de cola / trazas de error"
            )
        elif claim.conflict_detected:
            body = (
                f"**CONFLICT MODE**\n"
                f"The runtime shows non-nominal state, but current metrics do not isolate a single root cause.\n"
                f"**Possible causes:**\n"
                f"- module bus latency\n"
                f"- state sync delay\n"
                f"More evidence required."
            )
        else:
            # Evidence Mode
            evidence_lines = "\n".join([f"- {i.source} {i.key} = {i.value}" for i in claim.supporting_evidence])
            limitations_lines = "\n".join([f"- {l}" for l in claim.limitations]) or "None"
            
            body = (
                f"**EVIDENCE**\n{evidence_lines}\n\n"
                f"**HYPOTHESIS**\n{claim.claim}\n\n"
                f"**CONFIDENCE**\n{claim.confidence}\n\n"
                f"**LIMITATION**\n{limitations_lines}\n\n"
                f"**NEXT STEP**\nInvestigar la capa afectada para confirmar la causa raíz."
            )

        return AICommandResponse(
            intent="evidence_grounded_reasoning",
            status="success",
            message=body,
            payload={"evidence": bundle.items, "confidence": claim.confidence}
        )

    async def _process_analysis(self, msg: str, lang: str, system_state: Any, plan: Any, evidence_bundle: Optional[Any] = None, completed_steps: Optional[List[str]] = None, source_surface: str = "chat") -> AICommandResponse:
        """
        Structured Reasoning using actual system state and detailed plan.
        """
        # Step 1: ANALYSIS & RE-PLANNING (Now based on MATHEMATICAL TRUTH)
        diagnosis = None
        hypothesis_id = None
        snapshot_id = evidence_bundle.snapshot_id if evidence_bundle else None
        evidence_items = evidence_bundle.items if evidence_bundle else None
        
        if evidence_bundle:
             # Disparamos la Verdad Local
             from .reasoning.runtime_truth import runtime_truth
             diagnosis = runtime_truth.evaluate(evidence_bundle, request_msg=msg)
             analysis_body = diagnosis.claim
             hypothesis_id = diagnosis.hypothesis_id
             
             # RE-PLAN (Overriding the initial generic plan with a real operative one)
             from .planner.task_planner import task_planner
             plan = task_planner.create_plan_from_diagnosis(diagnosis, lang)
             
             # Sync with Persistent Mission State
             active_mission = mission_manager.get_active_mission()
             if not active_mission or active_mission.active_goal != plan.goal:
                 mission_manager.create_mission(
                     goal=plan.goal,
                     plan_id=diagnosis.hypothesis_id,
                     pending_steps=[str(s.id) for s in plan.steps],
                     plan=plan
                 )
             else:
                 # Si ya existe y es compatible, nos aseguramos que esté OPEN
                 mission_manager.set_status(MissionStatus.OPEN)
             
             # VERIFY (The new local guard)
             from .reasoning.verification_layer import verification_layer
             verification = verification_layer.verify(diagnosis, plan)
             
             if not verification.is_overall_valid:
                 analysis_body += f"\n\n**VERIFICATION FAILED**: {', '.join(verification.global_notes)}"
             
             # Usar la evidencia refinada del diagnóstico para la ejecución
             evidence_items = diagnosis.supporting_evidence
        else:
             analysis_body = self._conduct_analysis(msg, lang, system_state)

        
        # Step 2: PLAN & ACTION STATUS (Grounded)
        if not plan:
            return AICommandResponse(intent="chat", status="success", message="No tengo un plan cargado para esta operación.")
            
        plan_body = "\n".join([f"{s.id}. {s.description}" for s in plan.steps])
        
        # Step 3: EXECUTION (Stage 8: Controlled Execution Layer)
        # Solo ejecutamos si la verificación no bloqueó el plan
        execution_result = {"status": "BLOCKED", "steps_completed": [], "current_step": 0}
        if evidence_bundle and verification.verification_mode != "blocked":
            execution_result = await execution_controller.run(
                plan, 
                evidence=evidence_items, 
                hypothesis_id=hypothesis_id, 
                snapshot_id=snapshot_id
            )
        elif not evidence_bundle:
            # Fallback for manual analysis or continuation
            execution_result = await execution_controller.run(plan, steps_already_completed=completed_steps)

        
        # Step 4: CHIP STATUS (Stage 9: Orchestrator Layer)
        chip_statuses = chip_orchestrator.get_all_chips_status()
        chip_report = "\n".join([f"{c['chip_id']}: {c['status']}" for c in chip_statuses[:5]]) # Limit to 5 for UI

        # Step 5: FINAL SYNTHESIS (The official mouth of OmniWeb)
        # Delegamos la construcción técnica a la capa de síntesis especializada
        from .orchestration.executive_synthesis import executive_synthesis
        
        response_text = executive_synthesis.synthesize_analysis(
            diagnosis=diagnosis if evidence_bundle else None,
            plan=plan,
            verification=verification if evidence_bundle else None,
            execution_result=execution_result,
            chip_report=chip_report,
            lang=lang,
            query=msg,
            surface=source_surface
        )

        return AICommandResponse(
            intent="creator_analysis",
            status="success",
            message=response_text,
            payload={
                "brain_execution": True, 
                "plan": plan.to_dict(),
                "execution_state": execution_result,
                "health_applied": getattr(system_state, 'health', 'unknown') if system_state else 'unknown'
            }
        )


    def _conduct_analysis(self, msg: str, lang: str, system_state: Any) -> str:
        health_obj = getattr(system_state, 'health', None)
        health = health_obj.value if health_obj else "nominal"
        
        if "rendimiento" in msg or "cuello de botella" in msg or "bottleneck" in msg:
             diag = "He detectado una latencia inusual en el bus de módulos." if lang == "es" else "I've detected unusual latency in the module bus."
             if health != "healthy":
                 diag += f" El estado del sistema en {health.upper()} confirma la degradación de performance." if lang == "es" else f" System state in {health.upper()} confirms performance degradation."
             return diag

        if "comprend" in msg or "comprensión" in msg:
             return "El sistema actualmente depende de patrones estáticos de regex. Esto limita la interpretación semántica." if lang == "es" else "The system currently relies on static regex patterns. This limits semantic interpretation."
        
        return f"El sistema se encuentra en estado {health.upper()}. Se observa una falta de razonamiento contextual controlado por el semantic buffer." if lang == "es" else f"The system is in {health.upper()} state. A lack of contextual reasoning controlled by semantic buffer is observed."

    def _decide_action(self, msg: str, lang: str) -> str:
        return "He activado el modo de observación profunda en el logger del AI Host." if lang == "es" else "I've activated deep observation mode in the AI Host logger."

    def _define_verification(self, msg: str, lang: str) -> str:
        return "Comparar tiempos de respuesta con el benchmark actual del sistema." if lang == "es" else "Compare response times with the current system benchmark."

    def _generate_natural_fallback(self, lang: str) -> AICommandResponse:
        """DEPRECATED: Use executive_synthesis.synthesize_honest_feedback instead."""
        from .orchestration.executive_synthesis import executive_synthesis
        return AICommandResponse(intent="chat", status="success", message=executive_synthesis.synthesize_honest_feedback("uncertainty", lang))

    def _detect_cognitive_query(self, msg: str) -> bool:
        """Detects requests for the shared cognitive core state."""
        keywords = [
            "hypothesis", "hipótesis", "world model", "modelo de mundo",
            "evaluating", "evaluando", "omni is currently", "omni está actualmente",
            "evidence produced your last plan", "evidencia produjo tu último plan",
            "active chips", "chips activos", "system state", "estado del sistema"
        ]
        return any(k in msg for k in keywords)

    async def _handle_cognitive_query(self, msg: str, lang: str) -> AICommandResponse:
        """Queries the Cognitive Core for unified reality model."""
        try:
            from .cognition.cognitive_core import cognitive_core
        except ImportError:
            return AICommandResponse(intent="error", status="error", message="Cognitive Core service is genuinely unavailable.")
        
        # 1. Hypothesis Query
        if any(w in msg for w in ["hypothesis", "hipótesis", "evaluating", "evaluando"]):
            hypotheses = cognitive_core.get_active_hypotheses()
            if not hypotheses:
                # Try to find recent evaluated ones
                all_h = list(cognitive_core.hypotheses.values())
                if all_h:
                    last_h = sorted(all_h, key=lambda x: x.timestamp, reverse=True)[0]
                    body = (
                        f"I am not evaluating any active hypothesis right now.\n"
                        f"**Latest processed:** {last_h.description}\n"
                        f"**Status:** {last_h.status.upper()}\n"
                        f"**Final Confidence:** {last_h.confidence}"
                    ) if lang == "en" else (
                        f"No estoy evaluando ninguna hipótesis activa ahora mismo.\n"
                        f"**Última procesada:** {last_h.description}\n"
                        f"**Estado:** {last_h.status.upper()}\n"
                        f"**Confianza final:** {last_h.confidence}"
                    )
                    return AICommandResponse(intent="cognitive_query", status="success", message=body)
                
                body = "I am not currently evaluating any technical hypotheses." if lang == "en" else "No estoy evaluando ninguna hipótesis técnica actualmente."
                return AICommandResponse(intent="cognitive_query", status="success", message=body)
            
            h = hypotheses[0]
            body = (
                f"**Hypothesis:**\n{h.description}\n\n"
                f"**Confidence:**\n{h.confidence}\n\n"
                f"**Evidence:**\n- " + "\n- ".join(h.supporting_evidence)
            )
            return AICommandResponse(intent="cognitive_query", status="success", message=body, payload=h.dict())

        # 2. World Model Query
        if any(w in msg for w in ["world model", "modelo de mundo", "system state", "active chips"]):
            model = cognitive_core.get_latest_world_model()
            ws = model["world_state"]
            
            body = (
                f"**SYSTEM STATE**\n"
                f"Health: {ws['system_health']}\n"
                f"Active Chips: {', '.join(ws['active_chips']) or 'None'}\n"
                f"Snapshot: {ws['runtime_snapshot_timestamp']}\n\n"
                f"**ACTIVE HYPOTHESES**\n" + 
                ("\n".join([f"- {h['description']} (Conf: {h['confidence']})" for h in model['active_hypotheses']]) or "None")
            )
            return AICommandResponse(intent="cognitive_query", status="success", message=body, payload=model)

        # 3. Evidence Traceability Query
        if any(w in msg for w in ["last plan", "último plan", "evidencia"]):
            history = cognitive_core.execution_history
            if not history:
                 return AICommandResponse(intent="cognitive_query", status="success", message="No execution history found in the current session.")
            
            last = history[-1]
            body = (
                f"**PLAN TRACEABILITY**\n"
                f"Plan ID: {last.plan_id}\n"
                f"Outcome: {last.outcome}\n\n"
                f"**EVIDENCE BUNDLE**\n" +
                ("\n".join([f"- {e}" for e in last.evidence_used]) or "No captured evidence used.")
            )
            return AICommandResponse(intent="cognitive_query", status="success", message=body, payload=last.dict())

        return self._generate_natural_fallback(lang)

    def _detect_learning_query(self, msg: str) -> bool:
        """Detects requests for learning stats and patterns."""
        keywords = [
            "learning", "aprendizaje", "reliability", "confiabilidad",
            "patterns", "patrones", "patrón", "patron", "what have you learned", "qué has aprendido",
            "accuracy", "exactitud", "calibration", "calibración", "calibracion",
            "increased or decreased", "aumentó o disminuyó", "aumento o disminuyo",
            "hypotheses evaluation", "diagnostic failure", "diagnóstico fallido", "diagnostico fallido"
        ]
        return any(k in msg for k in keywords)

    async def _handle_learning_query(self, msg: str, lang: str) -> AICommandResponse:
        """Queries the Adaptive Learning layer with structured response modes."""
        try:
            from .learning.adaptive_learning import adaptive_learning
            from .cognition.cognitive_core import cognitive_core
        except ImportError:
            return AICommandResponse(intent="error", status="error", message="Adaptive Learning service is unavailable.")
        
        report = adaptive_learning.get_reliability_report()
        rel = report["evidence_reliability"]
        history = adaptive_learning.learning_history
        
        # 1. CONFIDENCE CHANGES
        if any(w in msg for w in ["increased", "decreased", "aumentó", "aumento", "disminuyó", "disminuyo", "confianza", "confidence"]):
             if not history:
                 return AICommandResponse(intent="learning_query", status="success", message="No hay datos de aprendizaje suficientes todavía.")
             
             # Looking for records with hypothesis
             h_records = [r for r in history if r.hypothesis_id]
             if not h_records:
                 return AICommandResponse(intent="learning_query", status="success", message="He registrado ejecuciones, pero ninguna ligada a una hipótesis técnica para calibrar.")

             latest = h_records[-1]
             h = cognitive_core.hypotheses.get(latest.hypothesis_id)
             h_desc = h.description if h else "Unknown Hypothesis"
             
             # Success +0.1, Failure -0.2, Partial -0.05
             # Logic mapping for presentation
             delta = 0.1 if latest.execution_outcome == "COMPLETED" else (-0.2 if latest.execution_outcome == "FAILED" else -0.05)
             
             body = (
                 f"**LEARNING**\n"
                 f"- hypothesis: {h_desc}\n"
                 f"- last outcome: {latest.execution_outcome}\n"
                 f"- confidence change: {delta:+.2f} (Current: {h.confidence if h else 'N/A'})\n\n"
                 f"**TRACEABILITY**\n"
                 f"Plan ID: {latest.plan_id}\n"
                 f"Snapshot ID: {latest.evidence_snapshot_id or 'N/A'}"
             )
             return AICommandResponse(intent="learning_query", status="success", message=body)

        # 2. LEARNING FROM FAILURE
        if any(w in msg for w in ["fallido", "parcial", "failed", "partial"]):
             bad_outcomes = [r for r in history if r.execution_outcome in ["FAILED", "PARTIAL"]]
             if not bad_outcomes:
                 return AICommandResponse(intent="learning_query", status="success", message="No se han registrado diagnósticos fallidos o parciales en esta sesión.")
             
             latest_bad = bad_outcomes[-1]
             body = (
                 f"**LEARNING**\n"
                 f"Del último resultado {latest_bad.execution_outcome}, he aprendido que la correlación entre las métricas observadas y el éxito del plan fue baja ({latest_bad.success_score}).\n"
                 f"He ajustado la confiabilidad de las fuentes de evidencia involucradas para futuras calibraciones.\n\n"
                 f"**TRACEABILITY**\n"
                 f"Plan ID: {latest_bad.plan_id}"
             )
             return AICommandResponse(intent="learning_query", status="success", message=body)

        # 3. PATTERNS
        if any(w in msg for w in ["pattern", "patrón", "patron", "patrones"]):
             patterns = adaptive_learning.model.pattern_correlations
             if not patterns:
                 return AICommandResponse(intent="learning_query", status="success", message="No hay datos de aprendizaje suficientes todavía para extraer patrones.")
             
             lines = []
             for metric, stats in list(patterns.items())[:3]:
                 impact = stats.get("weighted_impact", 0.0)
                 desc = "correlaciona con éxito" if impact > 0 else "correlaciona con fallos"
                 lines.append(f"- {metric} {desc} (Impacto: {impact})")
                 
             body = (
                 f"**PATTERN**\n" + ("\n".join(lines) or "No clear patterns detected yet.") + "\n\n"
                 f"**LIMITATION**\n"
                 f"Learning history depth: {len(history)} samples."
             )
             return AICommandResponse(intent="learning_query", status="success", message=body)

        # 4. EVIDENCE RELIABILITY
        if any(w in msg for w in ["reliability", "confiabilidad", "confiabilidad", "evidence", "evidencia"]):
            lines = [f"- source: {k}\n  reliability: {v:.2f}" for k, v in list(rel.items())[:5]]
            body = (
                f"**RELIABILITY REPORT**\n"
                f"How much I trust specific data sources based on past outcomes:\n\n" +
                ("\n\n".join(lines) or "No reliability data collected yet.")
            )
            return AICommandResponse(intent="learning_query", status="success", message=body, payload=rel)

        # Default summary
        body = (
            f"**ADAPTIVE LEARNING LAYER**\n"
            f"Records processed: {len(history)}\n\n"
            f"Please ask specifically about: confidence changes, patterns, or reliability."
        )
        return AICommandResponse(intent="learning_query", status="success", message=body)

    def _detect_mode(self, msg: str, intent: str, source_surface: str = "chat") -> str:
        """Detects if we should be in Conversational or Technical reasoning mode."""
        
        # 0. Workspace Bias: If in cockpit/workspace, we default to technical unless pure smalltalk
        if source_surface == "workspace":
             active = mission_manager.get_active_mission()
             if active and active.status == MissionStatus.OPEN:
                  smalltalk_full = {"hola", "quien eres", "quién eres", "gracias", "chau", "adiós"}
                  if msg in smalltalk_full and len(msg.split()) == 1:
                       return "conversational"
                  return "technical"
        
        # 1. Surface Override (Chat demands clean voice)
        if source_surface == "chat":
             # Special tech triggers for chat
             tech_triggers = ["por qué", "por que", "analiza", "diagnosis", "error", "fallo", "roadmap", "plan", "evidence"]
             if any(w in msg.lower() for w in tech_triggers) or intent in ["creator_analysis", "creator_plan"]:
                  return "technical"
             return "conversational"

        # 2. Workspace / Default Logic
        tech_keywords = [
            "analiza", "analyze", "why", "por qué", "qué pasa", "error", 
            "problem", "evidence", "plan", "fix", "repara", "diagnóstico",
            "métrica", "metric", "hypothesis", "hipótesis"
        ]
        if any(w in msg for w in tech_keywords) or intent in ["creator_analysis", "creator_plan", "evidence_grounded_reasoning"]:
            return "technical"
        
        return "conversational"

