import logging
import os
import uuid
import time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .mutation_engine import mutation_engine, MutationBatch, FileOperation, MutationType
from .patch_preview import patch_preview_engine, PatchPreview
from ..planner.task_planner import TaskPlan

logger = logging.getLogger(__name__)

class ActionPlan(BaseModel):
    """
    Structured action proposal for code mutations.
    Connects reasoning output to the File Mutation Engine.
    """
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent: str
    target_files: List[str]
    proposed_changes: List[Dict[str, str]] # List of {"path": str, "content": str, "op": str}
    confidence_score: float = 0.9
    risk_level: str = "LOW" # LOW, MEDIUM, HIGH

class ActionExecutionBridge:
    """
    Bridging layer between AI Reasoning (Omni) and File Mutations.
    Ensures safety, approval, and traceability.
    """
    
    PROTECTED_FILES = [".env", "omniweb.db", "auth_tokens", "secrets", "database"]

    def __init__(self):
        self.active_proposals: Dict[str, ActionPlan] = {}

    def _is_file_blocked(self, file_path: str) -> bool:
        """Safety check for sensitive system files."""
        p = file_path.lower()
        # Block specific extensions or names
        if p.endswith(".env") or "secrets" in p or "token" in p or p.endswith(".db"):
            return True
        
        # Block keywords
        for keyword in self.PROTECTED_FILES:
            if keyword in p:
                return True
        return False

    async def propose_action(self, action: ActionPlan, task_id: Optional[str] = None) -> PatchPreview:
        """
        Translates an ActionPlan into a PatchPreview for Creator approval.
        """
        logger.info(f"[ACTION_BRIDGE] Proposing action for intent: {action.intent}")
        
        # 1. Safety Filter
        for file_op in action.proposed_changes:
            if self._is_file_blocked(file_op["path"]):
                raise PermissionError(f"Safety Violation: Modification of sensitive file blocked - {file_op['path']}")

        # 2. Convert ActionPlan to MutationBatch
        ops = []
        for change in action.proposed_changes:
            op_type = MutationType.PATCH_FILE
            if change.get("op") == "CREATE": op_type = MutationType.CREATE_FILE
            elif change.get("op") == "DELETE": op_type = MutationType.DELETE_FILE
            elif change.get("op") == "MODIFY": op_type = MutationType.MODIFY_FILE

            ops.append(FileOperation(
                path=change["path"],
                op_type=op_type,
                content=change.get("content")
            ))

        batch = MutationBatch(
            id=action.plan_id,
            task_id=task_id or action.plan_id,
            operations=ops,
            origin="OmniAI"
        )

        # 3. Generate Preview (This persists it as PENDING)
        preview = patch_preview_engine.generate_preview(
            task_id=batch.task_id,
            module_id="ai_host",
            batch=batch
        )
        
        self.active_proposals[preview.id] = action
        logger.info(f"[ACTION_BRIDGE] Patch Preview {preview.id} generated and awaiting approval.")
        
        return preview

    async def execute_approved(self, preview_id: str) -> Dict[str, Any]:
        """
        Applies a previously approved patch and records the result.
        """
        preview = await patch_preview_engine.get_preview(preview_id)
        if not preview:
            return {"success": False, "error": "Preview not found."}
        
        if preview.status != "APPROVED":
            # Check if it was just approved in this call (simulated)
            # In a real UI flow, this is updated via an API endpoint
            logger.info(f"[ACTION_BRIDGE] Preview {preview_id} is {preview.status}. Approval required.")
            return {"success": False, "error": f"Preview must be APPROVED. Current status: {preview.status}"}

        # 1. Execute Mutation
        success, reload_results = await mutation_engine.execute_batch(preview.batch)
        
        if success:
            logger.info(f"[ACTION_BRIDGE] Mutation {preview_id} applied successfully.")
            # Record outcome (learning part happens here or in ExecutionController)
            return {
                "success": True, 
                "plan_id": preview.batch.id,
                "files_affected": [op.path for op in preview.batch.operations],
                "reload_status": reload_results
            }
        else:
            logger.error(f"[ACTION_BRIDGE] Mutation {preview_id} failed and was rolled back.")
            return {"success": False, "error": "Mutation failed. Check engine logs for details."}

    async def reject_action(self, preview_id: str):
        """Marks a proposal as rejected."""
        await patch_preview_engine.decide(preview_id, approved=False)
        if preview_id in self.active_proposals:
            del self.active_proposals[preview_id]
        logger.info(f"[ACTION_BRIDGE] Proposal {preview_id} rejected by creator.")

action_execution_bridge = ActionExecutionBridge()
