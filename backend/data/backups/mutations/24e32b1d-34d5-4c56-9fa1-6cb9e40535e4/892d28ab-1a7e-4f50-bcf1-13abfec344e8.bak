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
        system_state: Optional[Any] = None
    ) -> Optional[AICommandResponse]:
        """
        Main reasoning entry point.
        """
        msg = message.lower().strip()
        lang = session_state.language
        
        # 0. MEMORY MANAGEMENT
        if any(w in msg for w in ["reset session memory", "limpia memoria", "reset memoria"]):
            semantic_memory.clear()
            msg_res = "Memoria de sesión limpiada correctamente." if lang == "es" else "Session memory cleared successfully."
            return AICommandResponse(intent="memory_reset", status="success", message=msg_res)

        # 1. SEMANTIC CONTEXT RETRIEVAL
        last_topic = semantic_memory.get_last_topic()
        last_intent = semantic_memory.get_last_intent()
        
        # 2. CATEGORIZATION
        intent = intent_classifier.classify(msg) or "unknown"
        
        # 3. CONTEXTUAL CONTINUITY (Follow-up handling)
        is_followup = (intent == "acknowledgment" or any(w in msg for w in ["continuemos", "dale", "seguimos", "follow up"]))
        if is_followup and last_topic:
             # Augment message for reasoning
             msg_enriched = f"{msg} (contexto: {last_topic})"
             logger.info(f"[BRAIN_CONTEXT] Follow-up detected. Enriched prompt: {msg_enriched}")
        else:
             msg_enriched = msg

        # Explicit System Status check
        if intent == "show_system_status":
             if any(w in msg for w in ["status", "estado", "salud", "diagnostic"]):
                 res = await self.command_router._handle_show_system_status(msg)
                 semantic_memory.add_interaction(msg, res.message, intent)
                 return res
             else:
                 intent = "creator_analysis"

        # 3.5. ADAPTIVE LEARNING QUERIES (Stage 12/13) - HIGH PRIORITY
        if self._detect_learning_query(msg):
             res = await self._handle_learning_query(msg, lang)
             semantic_memory.add_interaction(msg, res.message, intent)
             return res

        # 3.6. COGNITIVE CORE QUERIES (Stage 11)
        if self._detect_cognitive_query(msg):
             res = await self._handle_cognitive_query(msg, lang)
             semantic_memory.add_interaction(msg, res.message, intent)
             return res

        # 3.7. EVIDENCE-FIRST REASONING (Stage 10)
        if self._detect_evidence_request(msg):
             res = await self._handle_evidence_request(msg, lang)
             semantic_memory.add_interaction(msg, res.message, intent)
             return res

        # 4. PLANNER LAYER
        plan = None
        if self._is_complex_request(msg_enriched, intent):
            plan = task_planner.create_plan(msg_enriched, intent, lang)
            logger.info(f"[PLANNER] Task plan generated: {plan.goal}")

        # 5. BRAIN REASONING & EXECUTION
        # A. Analysis Logic (Diagnostic / Plan / Self-Edit)
        if plan and plan.type.value in ["diagnostic", "self_edit", "general"]:
            # Even for GENERAL plans, if it's complex, we use analysis reasoning
            evidence_bundle = None
            if plan.type.value in ["diagnostic", "self_edit"]:
                 evidence_bundle = await evidence_engine.collect_evidence()
                 
            res = await self._process_analysis(msg_enriched, lang, system_state, plan, evidence=evidence_bundle.items if evidence_bundle else None)
            semantic_memory.add_interaction(msg, res.message, intent)
            return res

        # B. Multi-step Chip/Action Logic
        if intent in ["open_chip", "inspect_chip", "focus_chip_runtime"] or (plan and plan.type.value == "chip_action"):
             from .routing.utils import extract_chip_target
             target = extract_chip_target(msg)
             
             # --- STAGE 13: Chip Orchestrator Safety Patch ---
             is_explicit_request = any(w in msg for w in ["abre el chip", "activa", "lanza el chip", "open chip", "launch"])
             is_valid = chip_orchestrator.is_valid_chip(target)
             
             if not is_valid and not is_explicit_request:
                 logger.info(f"[ROUTING_SAFETY] Rejected chip target '{target}'. Routing back to conversational path.")
                 # Fallback to chat if it wasn't an explicit command and target is invalid
                 chat_proc = self.command_router.registry.get_processor("chat")
                 res = await chat_proc.process(msg, context=context) if chat_proc else self._generate_natural_fallback(lang)
                 semantic_memory.add_interaction(msg, res.message, intent)
                 return res

             # Delegate to ChipOrchestrator
             await chip_orchestrator.activate_chip(target)
             
             exec_intent = intent if intent in ["open_chip", "inspect_chip", "focus_chip_runtime"] else "open_chip"
             res = await self.command_router.intents[exec_intent](msg)
             
             if plan:
                 status_report = "\n".join([f"{s.id}. {s.description} (READY)" for s in plan.steps])
                 res.message = f"**PLAN: {plan.goal}**\n{status_report}\n\n**CHIP ORCHESTRATION**\nTarget: {target} (ACTIVE)\n\n{res.message}"
             
             semantic_memory.add_interaction(msg, res.message, intent)
             return res

        # C. Memory Logic
        if intent in ["idea_captured", "log_entry", "search_knowledge"]:
             res = await self.command_router.intents[intent](msg)
             semantic_memory.add_interaction(msg, res.message, intent)
             return res

        # D. Conversational Logic (Using Memory for Better Replies)
        if intent in ["acknowledgment", "greeting", "identity", "status_check"] or intent == "chat" or intent == "unknown" or intent == "creator_plan":
             if is_followup and last_topic:
                 res_msg = f"Perfecto, seguimos con lo de '{last_topic}'. ¿Algún detalle específico que quieras ajustar?" if lang == "es" else f"Perfect, continuing with '{last_topic}'. Any specific details you'd like to adjust?"
                 res = AICommandResponse(intent="chat", status="success", message=res_msg)
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
        if lang == "es":
            msg = "Entendido, estoy procesando tu solicitud. ¿Hay algo específico sobre el sistema que quieras que analice o simplemente seguimos adelante?"
        else:
            msg = "Understood, I'm processing your request. Is there anything specific about the system you'd like me to analyze, or shall we simply keep going?"
        
        return AICommandResponse(intent="chat", status="success", message=msg)

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
