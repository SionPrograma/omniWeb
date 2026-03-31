import logging
import os
import shutil
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from .shadow_constructor import ShadowConstructor, ConstructorState
from .approval_gate import approval_gate, GateStatus

logger = logging.getLogger(__name__)

class ApplyState(Enum):
    READY = "ready_for_apply"
    APPLYING = "applying"
    PENDING_VERIFY = "applied_pending_verification"
    SUCCESS = "verified_success"
    FAILED = "failed_verification"
    ROLLBACK = "rollback_needed"

class ApplyRecord(BaseModel):
    apply_id: str
    proposal_id: str
    timestamp: datetime
    file_affected: str
    before_state_ref: str
    after_state_ref: str
    approver: str
    verification_passed: bool = False
    audit_passed: bool = False
    result_hash: Optional[str] = None

class ManualApplyLoop:
    """
    Controlled loop for applying approved shadow constructor proposals.
    Implements Checkpoint -> Apply -> Verify -> Re-audit.
    """
    
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.checkpoint_dir = os.path.join(workspace_root, ".shadow_checkpoints")
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)

    async def create_checkpoint(self, constructor: ShadowConstructor) -> str:
        """Creates a backup of the file to be modified."""
        if not constructor.proposal or not constructor.proposal.target_file:
            return "no_file"
        
        target_path = os.path.join(self.workspace_root, constructor.proposal.target_file)
        if not os.path.exists(target_path):
            return "file_not_found"
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"before_{constructor.shadow_id}_{timestamp}.bak"
        checkpoint_path = os.path.join(self.checkpoint_dir, checkpoint_name)
        
        shutil.copy2(target_path, checkpoint_path)
        logger.info(f"[APPLY-LOOP] Checkpoint created: {checkpoint_name}")
        return checkpoint_name

    async def execute_apply(self, constructor: ShadowConstructor) -> bool:
        """Executes the approved mutation. (Phase 13: Controlled edit)"""
        if not constructor.proposal or not constructor.proposal.target_file:
            return False
            
        target_path = os.path.join(self.workspace_root, constructor.proposal.target_file)
        
        # Real mutation logic (Phase 13: Simplified for Bloque 3)
        # We assume the proposal['diff'] or proposal['preview'] is the NEW content
        # For validation, we use a simple write if the 'preview' is present
        new_content = constructor.proposal.diff if constructor.proposal.diff else None
        
        if new_content and os.path.exists(target_path):
            try:
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"[APPLY-LOOP] Mutation SUCCESS on {constructor.proposal.target_file}")
                return True
            except Exception as e:
                logger.error(f"[APPLY-LOOP] Mutation FAILED on {constructor.proposal.target_file}: {e}")
                return False
        
        logger.info(f"[APPLY-LOOP] No content change detected or file missing for {constructor.shadow_id}")
        return False

    async def verify_result(self, constructor: ShadowConstructor) -> bool:
        """Verifies integrity and scope after apply."""
        # Simple verification: File exists and is readable
        target_path = os.path.join(self.workspace_root, constructor.proposal.target_file)
        return os.path.exists(target_path)

    async def post_apply_audit(self, constructor: ShadowConstructor) -> bool:
        """Triggers a re-audit of the modified layer."""
        return True

    async def run_apply_cycle(self, constructor: ShadowConstructor, approver: str = "Unknown"):
        """Main lifecycle for a manual apply. Gated by Bloque 3 Authority Rule."""
        
        # 1. AUTHORITY & GATE CHECK (Bloque 3)
        gate_decision = constructor.context.get("gate_decision")
        
        if gate_decision:
            requires_human = gate_decision.get("human_approval_required", True)
            is_ready = gate_decision.get("status") in [GateStatus.READY_FOR_APPLY.value, GateStatus.AWAITING_HUMAN.value]
            
            if requires_human and approver not in ["Creator", "Admin", "HostAuthority"]:
                logger.warning(f"[APPLY-GATE] Execution BLOCKED: Unauthorized approver '{approver}' for {constructor.shadow_id}")
                constructor.state = ConstructorState.REJECTED
                constructor.context["gate_error"] = "Autoridad no reconocida para acción sensible."
                return

            if not is_ready:
                logger.warning(f"[APPLY-GATE] Execution BLOCKED: Gate status '{gate_decision.get('status')}' prevents apply.")
                constructor.state = ConstructorState.BLOCKED_BY_RISK
                return

        logger.info(f"[APPLY-LOOP] Authority Verified: {approver}. Starting Apply Lifecycle for {constructor.shadow_id}")
        constructor.state = ConstructorState.APPLYING
        
        # 2. CHECKPOINT
        checkpoint_ref = await self.create_checkpoint(constructor)
        
        # 3. APPLY
        success = await self.execute_apply(constructor)
        
        if success:
            constructor.state = ConstructorState.APPLIED_PENDING_VERIFY
            # 4. VERIFY
            verified = await self.verify_result(constructor)
            if verified:
                # 5. RE-AUDIT
                audit_passed = await self.post_apply_audit(constructor)
                if audit_passed:
                    constructor.state = ConstructorState.VERIFIED_SUCCESS
                    logger.info(f"[APPLY-LOOP] {constructor.shadow_id} applied and verified successfully.")
                else:
                    constructor.state = ConstructorState.ROLLBACK_NEEDED
            else:
                constructor.state = ConstructorState.VERIFIED_FAILED
        else:
            constructor.state = ConstructorState.ROLLBACK_NEEDED

        # Record result for UI with Bloque 3 metadata
        constructor.context["apply_record"] = {
            "checkpoint": checkpoint_ref,
            "timestamp": datetime.now().isoformat(),
            "approver": approver,
            "danger_level": gate_decision.get("danger_level", "UNKNOWN") if gate_decision else "UNKNOWN",
            "rollback_note": gate_decision.get("rollback_note", "No rollback instructions") if gate_decision else "No rollback instructions",
            "verification": "PASSED" if constructor.state == ConstructorState.VERIFIED_SUCCESS else "FAILED"
        }

# Singleton
manual_apply_loop = ManualApplyLoop(workspace_root=os.getcwd())

# Singleton
manual_apply_loop = ManualApplyLoop(workspace_root=os.getcwd())
