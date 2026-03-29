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
    READY_FOR_APPLY = "ready_for_apply"
    REJECTED = "rejected"

class ApprovalGateDecision(BaseModel):
    proposal_id: str
    status: GateStatus
    risk_level: str
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
    
    def __init__(self, policy_engine: Any):
        self.policy_engine = policy_engine
        self.sensitive_layers = ["core/kernel", "security/auth", "core/permissions", "infrastructure/db"]

    def evaluate_proposal(self, constructor: ShadowConstructor) -> ApprovalGateDecision:
        if not constructor.proposal:
            return ApprovalGateDecision(
                proposal_id=constructor.shadow_id,
                status=GateStatus.BLOCKED_BY_RISK,
                risk_level="UNKNOWN",
                is_safe=False,
                blocking_reason="Propuesta incompleta (falta reporte o diff).",
                result_summary="BLOQUEADO: Propuesta sin datos."
            )

        proposal = constructor.proposal
        
        # 1. Check Mandatory Audit Review
        audit_confirmed = constructor.auditor_note is not None
        
        # 2. Check Security / Core Layers
        is_sensitive = any(layer in proposal.target_file or layer in constructor.target_layer 
                          for layer in self.sensitive_layers)
        
        # 3. Check Policy Contradiction
        # Assuming policy_engine has a check_safety method
        policy_allows = proposal.no_touch_zones_respected
        
        # 4. Determine Gate Status
        status = GateStatus.AWAITING_AUDIT
        blocking_reason = None
        is_safe = True
        
        if is_sensitive:
            status = GateStatus.ESCALATED
            blocking_reason = f"Afecta capa sensible: {constructor.target_layer}"
            is_safe = False
        elif not policy_allows:
            status = GateStatus.BLOCKED_BY_RISK
            blocking_reason = "Contradice la política de zonas blindadas (Forbidden Zones)."
            is_safe = False
        elif not audit_confirmed:
            status = GateStatus.AWAITING_AUDIT
            blocking_reason = "Falta revisión de Shadow Auditor obligatoria."
            is_safe = False
        else:
            status = GateStatus.AWAITING_HUMAN
            is_safe = True

        # Summary for UI
        if is_safe and status == GateStatus.AWAITING_HUMAN:
            summary = "LISTO PARA APROBACIÓN HUMANA"
        elif status == GateStatus.ESCALATED:
            summary = "ESCALADO A NIVEL 2 (SENSITIVO)"
        else:
            summary = f"BLOQUEADO: {blocking_reason}"

        return ApprovalGateDecision(
            proposal_id=constructor.shadow_id,
            status=status,
            risk_level=proposal.risk_assessment,
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
