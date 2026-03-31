import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from .shadow_constructor import ShadowConstructor, ConstructorState, ShadowConstructorProposal
from .shadow_auditor import ShadowState

logger = logging.getLogger(__name__)

class GateStatus(Enum):
    PROPOSED = "proposed"
    AWAITING_AUDIT = "awaiting_audit"
    AWAITING_HUMAN = "awaiting_human_approval"
    BLOCKED_BY_RISK = "blocked_by_risk"
    ESCALATED = "escalated"
    EXTREME = "extreme_risk_escalated"
    READY_FOR_APPLY = "ready_for_apply"
    REJECTED = "rejected"

class ApprovalGateDecision(BaseModel):
    proposal_id: str
    status: GateStatus
    requires_approval: bool = True
    danger_level: str # CRITICAL, HIGH, MEDIUM, LOW
    affected_targets: List[str]
    rollback_note: str
    is_safe: bool
    blocking_reason: Optional[str] = None
    audit_confirmed: bool = False
    human_approval_required: bool = True
    checkpoint_required: bool = True
    result_summary: str

class ApprovalGate:
    """
    Governance layer for validating shadow constructor proposals.
    Ensures that no change passes without structured validation.
    """
    
    def __init__(self, policy_engine: Any = None):
        self.policy_engine = policy_engine
        self.sensitive_layers = [
            "backend/core", "core/kernel", "security/auth", 
            "core/permissions", "infrastructure/db", "core/ai_host", 
            "core/orchestration", ".env", "main.py"
        ]

    def evaluate_proposal(self, constructor: "ShadowConstructor") -> ApprovalGateDecision:
        # (Preserving evaluate_proposal but ensuring it calls the unified logic)
        proposal = constructor.proposal
        if not proposal:
             return self.execute_governance_check(
                 intent=constructor.assigned_microtask,
                 targets=[constructor.target_layer or "shadow"],
                 action_type="shadow_draft",
                 risk_hint="UNKNOWN"
             )
        
        return self.execute_governance_check(
            intent=constructor.assigned_microtask,
            targets=[proposal.target_file] if proposal.target_file else [constructor.target_layer or "shadow"],
            action_type="mutation",
            risk_hint=proposal.risk_assessment,
            proposal_id=constructor.shadow_id,
            audit_confirmed=constructor.auditor_note is not None
        )

    def execute_governance_check(self, intent: str, targets: List[str], action_type: str, risk_hint: str = "MEDIUM", proposal_id: str = "gen_action", audit_confirmed: bool = False) -> ApprovalGateDecision:
        """
        Unified Governance Entry Point for ALL sensitive actions (Bloque 3).
        """
        # 1. Sensitivity Detection
        is_sensitive = any(any(layer in (t or "") for layer in self.sensitive_layers) for t in targets)
        is_risky_action = action_type.lower() in ["restart", "delete", "mutation", "remediation", "patch"]
        
        # 2. Risk Calculation
        danger_level = risk_hint.upper()
        if is_sensitive:
            danger_level = "CRITICAL" if any("core" in (t or "") for t in targets) else "HIGH"
        elif is_risky_action and danger_level == "LOW":
            danger_level = "MEDIUM"

        # 3. Status Determination
        status = GateStatus.AWAITING_HUMAN
        blocking_reason = None
        is_safe = True

        if danger_level == "EXTREME":
            status = GateStatus.EXTREME
            blocking_reason = "PELIGRO EXTREMO: Acción bloqueada por política de seguridad."
            is_safe = False
        elif is_sensitive and not audit_confirmed and action_type == "mutation":
            status = GateStatus.AWAITING_AUDIT
            blocking_reason = "Falta validación técnica (Shadow Audit) previa."
            is_safe = False
        elif is_sensitive:
            status = GateStatus.ESCALATED
            is_safe = False
        
        # 4. Final Metadata (Bloque 3)
        rollback = f"Restaurar configuración previa o checkpoint de seguridad."
        if proposal_id != "gen_action" and not proposal_id.startswith("swarm"):
            rollback = f"Restaurar desde checkpoint `.shadow_checkpoints/before_{proposal_id}_*.bak`"

        summary = f"GATED: {status.value.upper()} ({danger_level})"
        if is_safe and status == GateStatus.AWAITING_HUMAN:
            summary = "LISTO PARA APROBACIÓN HUMANA"

        return ApprovalGateDecision(
            proposal_id=proposal_id,
            status=status,
            requires_approval=True,
            danger_level=danger_level,
            affected_targets=targets,
            rollback_note=rollback,
            is_safe=is_safe,
            blocking_reason=blocking_reason,
            audit_confirmed=audit_confirmed,
            human_approval_required=True,
            checkpoint_required=True,
            result_summary=summary
        )

# Singleton instance
# Note: For real use, inject the actual policy engine
approval_gate = ApprovalGate(policy_engine=None)
