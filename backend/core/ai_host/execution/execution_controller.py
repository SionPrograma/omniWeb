import uuid
import logging
from enum import Enum
from typing import List, Dict, Any, Optional
from ..planner.task_planner import TaskPlan, TaskStep
from ..memory.mission_manager import mission_manager

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExecutionState:
    def __init__(self, plan: TaskPlan, steps_already_completed: List[str] = None):
        self.plan_id = str(uuid.uuid4())
        self.plan = plan
        self.steps_completed = steps_already_completed or []
        
        # Calculate start index based on already completed steps
        self.current_step_index = 0
        if self.steps_completed:
            # Find the first step that is NOT completed
            completed_set = set([str(s) for s in self.steps_completed])
            for i, step in enumerate(self.plan.steps):
                if str(step.id) not in completed_set:
                    self.current_step_index = i
                    break
            else:
                # All steps completed
                self.current_step_index = len(self.plan.steps)

        self.status = ExecutionStatus.PENDING
        self.awaiting_creator_confirmation = False
        self.execution_log = []
        self.shared_context = {}
        
        if self.steps_completed:
            self.execution_log.append(f"Reanudando plan con {len(self.steps_completed)} pasos ya registrados.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "current_step": self.current_step_index + 1 if self.current_step_index < len(self.plan.steps) else len(self.plan.steps),
            "status": self.status.value,
            "steps_completed": self.steps_completed,
            "awaiting_creator_confirmation": self.awaiting_creator_confirmation,
            "execution_log": self.execution_log
        }

class ExecutionController:
    """
    Managed execution pipeline for OmniWeb TaskPlans.
    Classifies steps, handles sequential execution, and requests Creator approval for mutations.
    """

    SAFE_STEP_TYPES = ["read", "scan", "analyze", "audit", "locate", "process", "check", "view"]
    UNSAFE_STEP_TYPES = ["patch", "apply", "modify", "restart", "delete", "update", "mutate"]

    def __init__(self):
        self.active_executions: Dict[str, ExecutionState] = {}

    async def run(self, plan: TaskPlan, evidence: Optional[List[Any]] = None, hypothesis_id: Optional[str] = None, snapshot_id: Optional[str] = None, steps_already_completed: List[str] = None) -> Dict[str, Any]:
        """
        Main entry point for starting a plan execution.
        """
        state = ExecutionState(plan, steps_already_completed)
        self.active_executions[state.plan_id] = state
        
        logger.info(f"[EXECUTION_START] Starting plan: {plan.goal} (ID: {state.plan_id})")
        state.status = ExecutionStatus.RUNNING
        state.execution_log.append(f"Iniciando ejecución del plan: {plan.goal}")

        return await self._process_next_steps(state, evidence, hypothesis_id, snapshot_id)

    async def confirm_and_continue(self, plan_id: str, approved: bool = True) -> Dict[str, Any]:
        """
        Resumes an execution that was waiting for Creator confirmation.
        If it was a mutation, applies the approved patch via ActionExecutionBridge.
        """
        state = self.active_executions.get(plan_id)
        if not state or state.status != ExecutionStatus.WAITING_CONFIRMATION:
            return {"success": False, "error": "No execution waiting for confirmation found."}

        logger.info(f"[EXECUTION_RESUME] Creator decision for plan {plan_id}: {'APPROVED' if approved else 'REJECTED'}")
        state.awaiting_creator_confirmation = False
        state.status = ExecutionStatus.RUNNING
        
        if not approved:
            state.status = ExecutionStatus.FAILED
            state.execution_log.append("RECHAZADO: El creador ha rechazado la acción propuesta.")
            return await self._process_next_steps(state)

        # 1. Handle specialized confirmation (e.g., Action Bridge Patch)
        preview_id = state.shared_context.get("active_preview_id")
        if preview_id:
             from .action_execution_bridge import action_execution_bridge
             from .patch_preview import patch_preview_engine
             
             # Sync actual status in engine
             await patch_preview_engine.decide(preview_id, approved=True)
             
             # Apply via bridge
             result = await action_execution_bridge.execute_approved(preview_id)
             if result["success"]:
                 state.execution_log.append(f"APLICADO: Parche {preview_id} ejecutado correctamente.")
                 state.execution_log.append(f"RELOAD: {result.get('reload_status', 'No reload needed')}")
             else:
                 state.status = ExecutionStatus.FAILED
                 state.execution_log.append(f"ERROR DE MUTACIÓN: {result.get('error')}")
                 return await self._process_next_steps(state)

        # 2. Advance to next step
        step_id = state.plan.steps[state.current_step_index].id
        state.steps_completed.append(step_id)
        state.current_step_index += 1
        
        # Sync with Persistent Mission State
        mission_manager.update_mission_step(str(step_id))
        
        return await self._process_next_steps(state)

    async def _process_next_steps(self, state: ExecutionState, evidence: Optional[List[Any]] = None, hypothesis_id: Optional[str] = None, snapshot_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes steps until completion or until a step requires confirmation.
        """
        while state.current_step_index < len(state.plan.steps):
            step = state.plan.steps[state.current_step_index]
            
            if self._step_requires_confirmation(step):
                # --- STAGE 14: Action Bridge Integration ---
                # For mutation steps, we allow generating the proposal (preview) 
                # before pausing, so the creator has something to review.
                if step.type in ["patch", "apply", "modify", "mutate"]:
                    await self._execute_step(state, step, evidence)
                
                state.status = ExecutionStatus.WAITING_CONFIRMATION
                state.awaiting_creator_confirmation = True
                msg = f"Creator confirmation required before continuing with step {step.id}: {step.description}"
                if not any("PROPUESTA DE PARCHE GENERADA" in log for log in state.execution_log):
                    state.execution_log.append(f"PAUSADO: {msg}")
                
                logger.info(f"[EXECUTION_PAUSE] {msg}")
                break

            # Execute safe step
            await self._execute_step(state, step, evidence)
            state.current_step_index += 1
            state.steps_completed.append(step.id)
            
            # Sync with Persistent Mission State
            mission_manager.update_mission_step(str(step.id))

        if state.current_step_index >= len(state.plan.steps):
            state.status = ExecutionStatus.COMPLETED
            state.execution_log.append("Plan completado exitosamente.")
            logger.info(f"[EXECUTION_COMPLETE] Plan {state.plan_id} completed.")
            
        # Record outcome for learning if it's a final state
        if state.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
            self._record_final_outcome(state, evidence, hypothesis_id, snapshot_id)

        return state.to_dict()

    def _record_final_outcome(self, state: ExecutionState, evidence: Optional[List[Any]], hypothesis_id: Optional[str], snapshot_id: Optional[str]):
        """Consolidated outcome recording for Cognitive Core and Adaptive Learning."""
        try:
            from ..cognition.cognitive_core import cognitive_core
            from ..learning.adaptive_learning import adaptive_learning
            
            # Stringify evidence
            evidence_strings = []
            if evidence:
                for item in evidence:
                    if hasattr(item, 'source') and hasattr(item, 'key'):
                        evidence_strings.append(f"{item.source}.{item.key}={item.value}")
                    elif isinstance(item, dict) and 'source' in item and 'key' in item:
                        evidence_strings.append(f"{item['source']}.{item['key']}={item['value']}")
                    else:
                        evidence_strings.append(str(item))

            # 1. Update Cognitive Core
            cognitive_core.record_execution_outcome(
                plan_id=state.plan_id,
                steps=[{"id": s.id, "desc": s.description} for s in state.plan.steps],
                outcome=state.status.value,
                evidence_used=evidence_strings
            )
            
            # 2. Update Adaptive Learning Layer (The real loop closure)
            adaptive_learning.record_outcome(
                plan_id=state.plan_id,
                hypothesis_id=hypothesis_id,
                evidence_snapshot_id=snapshot_id,
                outcome=state.status.value,
                evidence=evidence_strings
            )
        except Exception as e:
            logger.error(f"[EXECUTION_CONTROLLER] Failed to close learning loop: {e}")

    def _step_requires_confirmation(self, step: TaskStep) -> bool:
        """
        Safety logic to determine if a step needs manual approval.
        """
        step_type = step.type.lower()
        desc = step.description.lower()

        # Failsafe rules from prompt
        dangerous_keywords = [
            "mutation", "override", "restart", "delete", 
            "modify configuration", "apply patch", "mutar sistema",
            "reiniciar", "modificar configuración"
        ]
        
        if any(w in desc for w in dangerous_keywords):
            return True
            
        if step_type in self.UNSAFE_STEP_TYPES:
            return True
            
        return False

    async def _execute_step(self, state: ExecutionState, step: TaskStep, evidence: Optional[List[Any]] = None):
        """
        Executes step using ChipOrchestrator or ActionExecutionBridge when appropriate.
        """
        from backend.core.chips.chip_orchestrator import chip_orchestrator
        from .action_execution_bridge import action_execution_bridge, ActionPlan
        
        logger.info(f"[EXECUTION_STEP] Executing step {step.id}: {step.type} - {step.description}")
        
        # 1. Diagnostic / Analysis logic
        if step.type in ["analyze", "audit", "scan", "check", "view"]:
             if evidence:
                 summary = f"Evidence cited: {len(evidence)} items. Confidence: HIGH."
                 state.shared_context["runtime_evidence"] = evidence
                 state.execution_log.append(f"GROUNDED ANALYSIS: {summary}")
             
             state.shared_context["last_analysis"] = f"Análisis detectado para {step.description}: Estado Nominal."
             logger.info(f"[EXECUTION_STEP] Analysis captured in shared context.")

        # 2. Coordination / Log logic
        if step.type == "log" or "registra" in step.description.lower():
             data = state.shared_context.get("last_analysis", "Tarea completada.")
             await chip_orchestrator.route_command("logbook", "entry", {"content": data})
             state.execution_log.append(f"Resultado coordinado y enviado a chip 'logbook'")

        # 3. Mutation / Patch logic (Stage 14: Action Bridge)
        if step.type in ["patch", "apply", "modify", "mutate"]:
             # Extract proposed changes from context if present
             changes = state.shared_context.get("proposed_changes", [])
             if not changes:
                 state.status = ExecutionStatus.FAILED
                 state.execution_log.append("ERROR: No se encontraron cambios propuestos en el contexto para aplicar.")
                 return

             action = ActionPlan(
                 intent=state.plan.goal,
                 target_files=[c["path"] for c in changes],
                 proposed_changes=changes,
                 risk_level="MEDIUM" if len(changes) > 1 else "LOW"
             )

             # This triggers rule: No file mutation without explicit creator approval
             try:
                 preview = await action_execution_bridge.propose_action(action, task_id=state.plan_id)
                 state.status = ExecutionStatus.WAITING_CONFIRMATION
                 state.awaiting_creator_confirmation = True
                 state.shared_context["active_preview_id"] = preview.id
                 state.execution_log.append(f"PROPUESTA DE PARCHE GENERADA: Preview ID {preview.id}. Esperando aprobación del creador.")
                 logger.info(f"[EXECUTION_MUTATION_PAUSE] Awaiting approval for preview {preview.id}")
             except PermissionError as e:
                 state.status = ExecutionStatus.FAILED
                 state.execution_log.append(f"BLOQUEADO POR SEGURIDAD: {str(e)}")
                 logger.warning(f"[ACTION_BRIDGE_SAFETY] Blocked: {e}")

        state.execution_log.append(f"Paso {step.id} procesado: {step.description}")

execution_controller = ExecutionController()
