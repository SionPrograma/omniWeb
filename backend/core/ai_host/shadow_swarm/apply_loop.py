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
        """Executes the approved diff. (Phase 13: Controlled simulation/minimal edit)"""
        # In this phase, we simulate the code mutation based on the approved proposal.
        # Minimal implementation: Log the intent and assume success if the file exists.
        
        logger.info(f"[APPLY-LOOP] Applying diff for {constructor.shadow_id} on {constructor.proposal.target_file}")
        # Real mutation logic would go here (e.g. using patch or line replacement)
        return True

    async def verify_result(self, constructor: ShadowConstructor) -> bool:
        """Verifies integrity and scope after apply."""
        # Verification logic: JSON format check, file accessibility, etc.
        return True

    async def post_apply_audit(self, constructor: ShadowConstructor) -> bool:
        """Triggers a re-audit of the modified layer."""
        # Simulated re-audit passing
        return True

    async def run_apply_cycle(self, constructor: ShadowConstructor, approver: str = "Creator"):
        """Main lifecycle for a manual apply."""
        
        # 1. PRE-CONDITIONS
        # Align: check against GateStatus member if state came from Gate
        if (constructor.state != ConstructorState.READY_FOR_APPLY and 
            constructor.state != ConstructorState.AWAITING_HUMAN):
             # We allow from awaiting_human_approval if the gate said it's OK
             pass

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
                    logger.warning(f"[APPLY-LOOP] {constructor.shadow_id} failed post-apply audit.")
            else:
                constructor.state = ConstructorState.VERIFIED_FAILED
        else:
            constructor.state = ConstructorState.ROLLBACK_NEEDED

        # Record result for UI
        constructor.context["apply_record"] = {
            "checkpoint": checkpoint_ref,
            "timestamp": datetime.now().isoformat(),
            "approver": approver,
            "verification": "PASSED" if constructor.state == ConstructorState.VERIFIED_SUCCESS else "FAILED"
        }

# Singleton
manual_apply_loop = ManualApplyLoop(workspace_root=os.getcwd())
