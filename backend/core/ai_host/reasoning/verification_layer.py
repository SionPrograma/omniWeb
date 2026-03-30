from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from .runtime_truth import StructuredDiagnosis, DiagnosisCategory
from ..planner.task_planner import TaskPlan, ActionableTask, ActionType

class VerificationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    CONTRADICTORY = "contradictory"
    AMBIGUOUS = "ambiguous"
    HIGH_RISK = "high_risk"

class TaskVerification(BaseModel):
    task_id: int
    is_valid: bool
    status: VerificationStatus
    reject_reason: Optional[str] = None
    requires_approval: bool = False
    is_dangerous: bool = False

class VerificationResult(BaseModel):
    is_overall_valid: bool
    verification_mode: str # "safe_continue", "approval_required", "clarification", "blocked"
    task_verifications: List[TaskVerification] = Field(default_factory=list)
    global_notes: List[str] = Field(default_factory=list)
    final_diagnosis_ref: str

class VerificationLayer:
    """
    Local guard between Planning and Execution.
    Checks physical reality, contradictions, and safety.
    """
    def verify(self, diagnosis: StructuredDiagnosis, plan: TaskPlan) -> VerificationResult:
        # 1. Initialize result
        verifs = []
        is_overall_valid = True
        mode = "safe_continue"
        notes = []

        # 2. Cross-check Diagnosis vs Plan (Contradiction Check)
        has_mutation = any(t.is_dangerous or t.action_type in [ActionType.RESTART, ActionType.PATCH, ActionType.MODIFY, ActionType.CLEAN] for t in plan.tasks)
        
        if diagnosis.diagnosis_type == DiagnosisCategory.NOMINAL.value and has_mutation:
            is_overall_valid = False
            mode = "clarification"
            notes.append("CONTRADICCIÓN: El diagnóstico es NOMINAL pero el plan propone mutaciones de estado.")

        # 3. Individual Task Verification
        for task in plan.tasks:
            task_v = self._verify_single_task(task, diagnosis)
            verifs.append(task_v)
            
            if not task_v.is_valid:
                is_overall_valid = False
                if task_v.status == VerificationStatus.CONTRADICTORY:
                    mode = "clarification"
            
            # Risk escalation
            if task_v.requires_approval or task_v.is_dangerous:
                if mode != "clarification" and mode != "blocked":
                    mode = "approval_required"
            
            if task_v.status == VerificationStatus.INVALID:
                mode = "blocked"

        # 4. Final Verdict
        if diagnosis.clarification_needed:
            mode = "clarification"

        return VerificationResult(
            is_overall_valid=is_overall_valid,
            verification_mode=mode,
            task_verifications=verifs,
            global_notes=notes,
            final_diagnosis_ref=diagnosis.diagnosis_type
        )

    def _verify_single_task(self, task: ActionableTask, diagnosis: StructuredDiagnosis) -> TaskVerification:
        # Importación tardía para evitar círculo
        from backend.core.module_registry import module_registry
        
        status = VerificationStatus.VALID
        is_valid = True
        reason = None
        
        # A. Target Existence Check
        target = task.target_id
        core_targets = ["system", "user", "system_bus", "os_memory", "omni_cache", "gateway_bus"]
        
        if target not in core_targets:
            # Si no es core, debe ser un chip
            slug = target.replace("chip-", "")
            chip = module_registry.search_chip(slug)
            if not chip:
                return TaskVerification(
                    task_id=task.id, is_valid=False, status=VerificationStatus.INVALID,
                    reject_reason=f"Target '{target}' no encontrado en el registro de módulos."
                )

        # B. Rationality / Contradiction Check
        if task.action_type == ActionType.RESTART and diagnosis.diagnosis_type == DiagnosisCategory.MEMORY_SATURATION.value:
            if "memory" not in task.target_id.lower() and "cache" not in task.target_id.lower():
                status = VerificationStatus.CONTRADICTORY
                reason = "Intento de reinicio de componente no relacionado con la saturación de memoria."

        # C. Safety Check
        is_dangerous = task.is_dangerous
        requires_approval = task.requires_approval
        
        return TaskVerification(
            task_id=task.id,
            is_valid=is_valid,
            status=status,
            reject_reason=reason,
            requires_approval=requires_approval,
            is_dangerous=is_dangerous
        )

verification_layer = VerificationLayer()
