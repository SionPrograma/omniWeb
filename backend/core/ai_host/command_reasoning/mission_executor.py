import logging
import asyncio
from typing import Dict, Any, List
from .mission_planner import MissionPlan, MissionStep
from ..shadow_swarm.shadow_orchestrator import shadow_orchestrator
from ..cognition.cognitive_core import cognitive_core

logger = logging.getLogger(__name__)

class MissionExecutor:
    """
    Coordinates the execution of validated mission plans using the Shadow Swarm.
    Bridges the reasoning engine with the distributed execution layer.
    """
    
    async def execute(self, plan: MissionPlan, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[MISSION_EXECUTOR] Dispatching mission to Shadow Swarm: {plan.title}")
        
        results = []
        
        # 1. TRIGGER THE SHADOW ORCHESTRATOR
        # We consolidate the mission plan into the orchestrator's domain
        mission_summary = (
            f"Goal: {plan.title}\n"
            f"Scale: {plan.scale}\n"
            f"Constraints: {', '.join(plan.constraints)}"
        )
        
        # The ShadowOrchestrator already handles Decompose -> Execute -> Audit -> Sync
        # We pass our pre-reasoned plan context to it
        extended_context = context.copy()
        extended_context["mission_plan"] = plan.dict()
        
        # 1.1 OPERATIONAL PIVOT (Phase 18)
        from ..memory.mission_manager import mission_manager
        active = mission_manager.get_active_mission()
        if active:
             params = active.parameters
             extended_context["audit_only"] = params.get("audit_only", False)
             extended_context["conservative_mode"] = params.get("conservative_mode", False)
             extended_context["roadmap_first"] = params.get("roadmap_first", False)
        
        # If it's roadmap_first, we stop here and return the plan for UI inspection
        if extended_context.get("roadmap_first"):
             logger.info(f"[EXECUTOR] Roadmap-first mode: Halting before swarm execution.")
             return {
                 "mission_title": plan.title,
                 "status": "awaiting_approval",
                 "execution_details": {"message": "Roadmap generado. Esperando revisión del Creador.", "plan": plan.dict()},
                 "audit_summary": ["Plan de misión listo para inspección."]
             }

        swarm_result = await shadow_orchestrator.execute_mission(plan.title, extended_context)
        
        # 2. GENERATE LEARNING RECORD
        self._record_learning(plan, swarm_result)
        
        return {
            "mission_title": plan.title,
            "status": swarm_result.get("status"),
            "execution_details": swarm_result,
            "audit_summary": swarm_result.get("results", {}).get("audit")
        }

    def _record_learning(self, plan: MissionPlan, result: Dict[str, Any]):
        """Consolidates mission outcome into Cognitive Core."""
        outcome = "COMPLETED" if result.get("status") == "success" else "FAILED"
        
        # 1. Basic Pattern Learning
        pattern = f"MISSION_EXECUTION_{plan.scale.upper()}"
        context_str = f"Plan: {plan.title} | Outcome: {outcome}"
        
        cognitive_core.add_learning_record(
            pattern=pattern,
            context=context_str,
            reliability=0.9 if outcome == "COMPLETED" else 0.4
        )
        
        # 2. Rich Mission Reasoning Record
        audit_findings = result.get("results", {}).get("audit", [])
        if isinstance(audit_findings, dict):
             # Extract list of found issues if audit_findings is the whole result dict
             audit_findings = audit_findings.get("findings", [])

        cognitive_core.add_mission_record(
            command=plan.creator_command,
            goal=plan.interpreted_goal,
            plan=plan.dict(),
            audit=audit_findings if isinstance(audit_findings, list) else [str(audit_findings)],
            outcome=outcome
        )
        
        logger.info(f"[MISSION_EXECUTOR] Learning record generated for: {plan.title}")

mission_executor = MissionExecutor()
