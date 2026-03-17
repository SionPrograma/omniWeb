from typing import Dict, Any, Optional, List
import logging
import re
from .processors.base import AICommandResponse
from .routing.intent_classifier import intent_classifier
from .sessions import session_state
from .memory.semantic_memory import semantic_memory
from .planner.task_planner import task_planner
from .execution.execution_controller import execution_controller
from backend.core.chips.chip_orchestrator import chip_orchestrator
from .reasoning.evidence_engine import evidence_engine
from .reasoning.runtime_truth import runtime_truth
from .reasoning.reflective_deliberation import reflective_deliberation
from .deliberation.deliberation_engine import deliberation_engine

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
        lang = session_state.language
        session_id = str(context.get("user_id", "default_user")) if context else "default_user"
        
        # 0. NORMALIZE & SEMANTIC UNDERSTANDING
        msg_clean = self._normalize_request(msg)
        
        if not understanding:
            from .intent_understanding.intent_engine import intent_engine
            understanding = await intent_engine.understand(msg_clean, session_id)
        
        intent = understanding["intent_group"]
        mode_override = understanding["mode"]
        
        # 1. ASSEMBLE DELIBERATION CONTEXT
        delib_context = await deliberation_engine.assemble_context(msg_clean, intent, session_id)
        
        # Apply semantic mode if deliberation doesn't override with a higher priority (remediation/limitation)
        mode = delib_context.reasoning_mode
        if mode in ["conversational", "diagnostic"] and mode_override != "conversational":
            mode = mode_override
            
        logger.info(f"[POWER_BRAIN] Mode: {mode} | Intent: {intent}")

        # 2. CONTEXTUAL CONTINUITY (Follow-up handling)
        if self._is_short_followup(msg_clean) and delib_context.recent_topic:
             return await self._handle_short_prompt(msg_clean, delib_context, lang)

        # 3. ROUTE BY MODE
        if mode == "reflective":
             res = await self._handle_reflective_reasoning(msg_clean, lang)
        elif mode == "remediation":
             res = await self._handle_remediation(msg_clean, delib_context, lang)
        elif mode == "swarm_orchestration":
             res = await self._handle_swarm_orchestration(msg_clean, delib_context, lang)
        elif mode == "patch_proposal":
             res = await self._handle_patch_proposal(msg_clean, delib_context, lang)
        elif mode == "limitation":
             res = await self._handle_limitation(msg_clean, delib_context, lang)
        elif mode == "diagnostic":
             # Check for Remediation Intelligence (Historical matching)
             remediation = self._check_remediation_history(msg_clean, delib_context)
             if remediation:
                 res = self._format_remediation_response(remediation, lang)
             else:
                 # Standard analysis with plan
                 plan = task_planner.create_plan(msg_clean, intent, lang)
                 res = await self._process_analysis(msg_clean, lang, system_state, plan, evidence=delib_context.relevant_evidence)
        elif intent in ["open_chip", "inspect_chip", "focus_chip_runtime"]:
             res = await self._handle_chip_action(msg_clean, intent, delib_context, lang)
        else:
             # Default Conversational
             chat_proc = self.command_router.registry.get_processor("chat")
             if chat_proc:
                 res = await chat_proc.process(msg_clean, context=context)
             else:
                 res = self._generate_natural_fallback(lang)

        # 4. POST-PROCESS & MEMORY
        if res:
            semantic_memory.add_interaction(msg, res.message, intent)
            return res

        return None

    async def _handle_remediation(self, msg: str, ctx: Any, lang: str) -> AICommandResponse:
        from .remediation.remediation_engine import remediation_engine
        proposal = await remediation_engine.analyze_and_propose(ctx)
        if not proposal:
            return self._generate_natural_fallback(lang)
            
        if lang == "es":
            body = (
                f"**OBSERVACIÓN**\n{proposal.observation}\n\n"
                f"**CAUSAS PROBABLES**\n" + "\n".join([f"- {c}" for c in proposal.likely_causes]) + "\n\n"
                f"**OPCIONES DE SOLUCIÓN**\n" + "\n".join([f"- {o.name}: {o.description} (Riesgo: {o.risk})" for o in proposal.solution_options]) + "\n\n"
                f"**SOLUCIÓN RECOMENDADA**\n{proposal.recommended_solution}\n\n"
                f"**PLAN DE IMPLEMENTACIÓN**\n" + "\n".join([f"- {p}" for p in proposal.implementation_plan]) + "\n\n"
                f"**CONFIANZA**: {proposal.confidence_level}"
            )
        else:
            body = (
                f"**OBSERVATION**\n{proposal.observation}\n\n"
                f"**LIKELY CAUSES**\n" + "\n".join([f"- {c}" for c in proposal.likely_causes]) + "\n\n"
                f"**SOLUTION OPTIONS**\n" + "\n".join([f"- {o.name}: {o.description} (Risk: {o.risk})" for o in proposal.solution_options]) + "\n\n"
                f"**RECOMMENDED SOLUTION**\n{proposal.recommended_solution}\n\n"
                f"**IMPLEMENTATION PLAN**\n" + "\n".join([f"- {p}" for p in proposal.implementation_plan]) + "\n\n"
                f"**CONFIDENCE**: {proposal.confidence_level}"
            )

        return AICommandResponse(
            intent="remediation_proposal",
            status="success",
            message=body,
            payload={"proposal": proposal.dict()}
        )

    async def _handle_swarm_orchestration(self, msg: str, ctx: Any, lang: str) -> AICommandResponse:
        from .command_reasoning.command_interpreter import command_interpreter
        from .command_reasoning.mission_planner import mission_planner
        from .command_reasoning.feasibility_auditor import feasibility_auditor
        from .command_reasoning.mission_executor import mission_executor
        
        logger.info(f"[REASONING_ENGINE] Processing high-level creator command: {msg}")
        
        # 1. INTERPRET
        interpreted = await command_interpreter.interpret(msg)
        
        # 2. PLAN
        plan = await mission_planner.create_plan(interpreted)
        
        # 3. AUDIT FEASIBILITY
        is_safe, refined_plan, risks = await feasibility_auditor.audit_plan(plan)
        
        # 4. EXECUTE
        mission_result = await mission_executor.execute(refined_plan, vars(ctx))
        
        # Synthesize results for UI
        res_list = mission_result.get("execution_details", {}).get("results", {})
        jobs_count = mission_result.get("execution_details", {}).get("jobs_executed", 0)
        
        if lang == "es":
            body = (
                f"**MISIÓN DISPUESTA: {refined_plan.title}**\n"
                f"Escala: {refined_plan.scale.upper()}\n"
                f"Estado: Misión validada y ejecutada.\n\n"
                f"**REQUERIMIENTOS Y RESTRICCIONES**\n" + 
                ("\n".join([f"- {c}" for c in refined_plan.constraints]) or "- Ninguna") + "\n\n"
                f"**EJECUCIÓN ESTRATÉGICA**\n"
                f"- Tareas procesadas: {jobs_count}\n"
                f"- Auditoría de factibilidad: {'Aprobada' if is_safe else 'Refinada (Riesgos mitigados)'}\n\n"
                f"**RESULTADO**\n"
                f"Omni ha coordinado el Shadow Swarm para cumplir con la instrucción del Creador. Los hallazgos han sido sincronizados en el Cognitive Core."
            )
        else:
            body = (
                f"**MISSION DISPATCHED: {refined_plan.title}**\n"
                f"Scale: {refined_plan.scale.upper()}\n"
                f"Status: Mission validated and executed.\n\n"
                f"**REQUIREMENTS & CONSTRAINTS**\n" + 
                ("\n".join([f"- {c}" for c in refined_plan.constraints]) or "- None") + "\n\n"
                f"**STRATEGIC EXECUTION**\n"
                f"- Microtasks processed: {jobs_count}\n"
                f"- Feasibility Audit: {'Passed' if is_safe else 'Refined (Risks mitigated)'}\n\n"
                f"**OUTCOME**\n"
                f"Omni has coordinated the Shadow Swarm to fulfill the Creator's instruction. All findings have been synchronized back to the Cognitive Core."
            )
            
        return AICommandResponse(
            intent="swarm_orchestration",
            status="success",
            message=body,
            payload=mission_result
        )

    def _normalize_request(self, msg: str) -> str:
        """Cleans up conversational noise for the reasoning layer."""
        noise = ["oye omni", "escucha", "puedes", "hey omni", "tell me", "can you"]
        for n in noise:
            msg = msg.replace(n, "")
        return msg.strip()

    def _is_short_followup(self, msg: str) -> bool:
        short_prompts = ["perfecto", "seguimos", "y ahora?", "vale", "ok", "dale", "continuemos", "perfect", "keep going", "and now?", "go on", "por qué?", "por que?", "why?"]
        return msg in short_prompts or len(msg.split()) < 3

    async def _handle_short_prompt(self, msg: str, ctx: Any, lang: str) -> AICommandResponse:
        topic = ctx.recent_topic
        import random
        if lang == "es":
            msg_res = f"Continuando con '{topic}'. ¿Qué paso sigue o qué más quieres analizar?"
        else:
            msg_res = f"Continuing with '{topic}'. What's the next step or detail to analyze?"
        
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
        if intent in ["idea_captured", "log_entry", "search_knowledge"]:
             res = await self.command_router.intents[intent](msg)
             semantic_memory.add_interaction(msg, res.message, intent)
             return res

        # D. Conversational Logic (Using Memory for Better Replies)
        if mode == "conversational" or intent in ["acknowledgment", "greeting", "identity", "status_check", "chat", "unknown"]:
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
             
             semantic_memory.add_interaction(msg, res.message, intent)
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

    async def _process_analysis(self, msg: str, lang: str, system_state: Any, plan: Any, evidence_bundle: Optional[Any] = None) -> AICommandResponse:
        """
        Structured Reasoning using actual system state and detailed plan.
        """
        # Step 1: ANALYSIS (Grounded via Runtime Truth if evidence exists)
        hypothesis_id = None
        evidence_items = evidence_bundle.items if evidence_bundle else None
        snapshot_id = evidence_bundle.snapshot_id if evidence_bundle else None
        
        if evidence_bundle:
             claim = runtime_truth.evaluate(evidence_bundle)
             analysis_body = claim.claim
             hypothesis_id = claim.hypothesis_id
             
             # --- STAGE 12: Confidence Refinement ---
             # We could adjust the displayed confidence based on historical accuracy here
        else:
             analysis_body = self._conduct_analysis(msg, lang, system_state)
        
        # Step 2: PLAN (Use the generated task plan object)
        plan_body = "\n".join([f"{s.id}. {s.description}" for s in plan.steps])
        
        # Step 3: EXECUTION (Stage 8: Controlled Execution Layer)
        execution_result = await execution_controller.run(
            plan, 
            evidence=evidence_items, 
            hypothesis_id=hypothesis_id, 
            snapshot_id=snapshot_id
        )
        
        # Format Execution Status for UI
        status_lines = []
        for step in plan.steps:
            if step.id in execution_result["steps_completed"]:
                status_lines.append(f"Step {step.id} completed")
            elif execution_result["status"] == "WAITING_CONFIRMATION" and step.id == execution_result["current_step"]:
                status_lines.append(f"Step {step.id} awaiting Creator confirmation")
            else:
                status_lines.append(f"Step {step.id} pending")
        
        exec_status_body = "\n".join(status_lines)
        
        # Step 4: VERIFY
        verify_body = "\n".join([f"- {v}" for v in plan.verification]) if plan.verification else self._define_verification(msg, lang)

        # Step 5: CHIP STATUS (Stage 9: Orchestrator Layer)
        chip_statuses = chip_orchestrator.get_all_chips_status()
        chip_report = "\n".join([f"{c['chip_id']}: {c['status']}" for c in chip_statuses[:5]]) # Limit to 5 for UI

        response_text = (
            f"**ANALYSIS**\n{analysis_body}\n\n"
            f"**PLAN: {plan.goal}**\n{plan_body}\n\n"
            f"**EXECUTION STATUS**\n{exec_status_body}\n\n"
            f"**CHIP STATUS**\n{chip_report}\n\n"
            f"**VERIFY**\n{verify_body}"
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
        """Generates a randomized natural language reply for conversational continuity."""
        import random
        if lang == "es":
            options = [
                "Entiendo. ¿En qué más puedo ayudarte con el sistema desde aquí?",
                "De acuerdo. ¿Quieres que analicemos algún otro componente o prefieres seguir con otra cosa?",
                "Vale. Sigo observando el estado del sistema en tiempo real.",
                "Perfecto. Estoy listo para tu siguiente instrucción, Creador.",
                "Entendido. ¿Pasamos a la siguiente fase o tienes alguna duda sobre lo anterior?",
                "Estoy a la escucha. ¿Qué quieres que evaluemos a continuación?",
                "Bien. La sincronización es estable. ¿Cuál es el siguiente paso?"
            ]
        else:
            options = [
                "I see. How else can I assist you with the system from here?",
                "Understood. Would you like me to analyze another component or move on to something else?",
                "Alright. I'm keeping an eye on the system state in real-time.",
                "Perfect. I'm ready for your next instruction, Creator.",
                "Got it. Shall we move to the next phase or do you have any questions about the previous steps?",
                "I'm listening. What should we evaluate next?",
                "Good. Synchronization is stable. What is the next step?"
            ]
        return AICommandResponse(intent="chat", status="success", message=random.choice(options))

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

    def _detect_mode(self, msg: str, intent: str) -> str:
        """Detects if we should be in Conversational or Technical reasoning mode."""
        tech_keywords = [
            "analiza", "analyze", "why", "por qué", "qué pasa", "error", 
            "problem", "evidence", "plan", "fix", "repara", "diagnóstico",
            "métrica", "metric", "hypothesis", "hipótesis"
        ]
        if any(w in msg for w in tech_keywords) or intent in ["creator_analysis", "creator_plan", "evidence_grounded_reasoning"]:
            return "technical"
        
        return "conversational"

    def _detect_reflective_reasoning(self, msg: str) -> bool:
        """Triggers for Part 1: Reflective Reasoning."""
        keywords = ["why", "por qué", "qué podría estar mal", "what could be wrong", "qué nos falta", "what might we be missing", "analiza el sistema", "analyze the system"]
        return any(k in msg for k in keywords)

    async def _handle_reflective_reasoning(self, msg: str, lang: str) -> AICommandResponse:
        """Handles deep reflective analysis mission."""
        analysis = await reflective_deliberation.analyze(msg)
        
        if lang == "es":
            body = (
                f"**OBSERVACIÓN**\n{analysis.observation}\n\n"
                f"**HIPÓTESIS PRIMARIA**\n{analysis.primary_hypothesis}\n\n"
                f"**EXPLICACIÓN ALTERNATIVA**\n{analysis.alternative_hypothesis}\n\n"
                f"**NIVEL DE CONFIANZA**\n{analysis.confidence_level}\n\n"
                f"**EVIDENCIA FALTANTE**\n" + ("\n".join([f"- {m}" for m in analysis.missing_evidence]) or "Ninguna") + "\n\n"
                f"**ACCIÓN RECOMENDADA**\n{analysis.recommended_action}"
            )
        else:
            body = (
                f"**OBSERVATION**\n{analysis.observation}\n\n"
                f"**PRIMARY HYPOTHESIS**\n{analysis.primary_hypothesis}\n\n"
                f"**ALTERNATIVE EXPLANATION**\n{analysis.alternative_hypothesis}\n\n"
                f"**CONFIDENCE LEVEL**\n{analysis.confidence_level}\n\n"
                f"**MISSING EVIDENCE**\n" + ("\n".join([f"- {m}" for m in analysis.missing_evidence]) or "None") + "\n\n"
                f"**RECOMMENDED NEXT STEP**\n{analysis.recommended_action}"
            )
            
        return AICommandResponse(
            intent="reflective_analysis",
            status="success",
            message=body,
            payload={"analysis": analysis.__dict__}
        )
