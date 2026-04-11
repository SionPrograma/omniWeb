import json
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.core.database import db_manager
from backend.core.governance.catalyst_policy_reviewer import catalyst_policy_reviewer
from backend.core.governance.catalyst_engine import catalyst_engine
from backend.core.governance.ledger_engine import governance_ledger_engine

logger = logging.getLogger(__name__)

class CatalystApplyService:
    """
    OMNIWEB — BLOQUE: OMNI_CATALYST_V0.6.
    Approved Refinement Apply Service.
    Handles atomic application and rollback of governance-approved catalyst refinements.
    """
    
    def __init__(self):
        from backend.core.config import settings
        self.policy_file = os.path.join(settings.DATA_DIR, "system", "catalyst_policy.json")
        self.backup_dir = os.path.join(settings.DATA_DIR, "backups", "catalyst_policy")
        os.makedirs(self.backup_dir, exist_ok=True)

    def apply_refinement(self, proposal_id: str, creator_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies a safe refinement proposal after Creator's explicit approval.
        """
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            # 1. Fetch proposal and validate safety
            proposals = catalyst_policy_reviewer.get_refinement_proposals()
            prop = next((p for p in proposals if p["proposal_id"] == proposal_id), None)
        
        if not prop:
            return {"status": "error", "message": "Proposal not found."}
        if not prop.get("is_apply_safe"):
            return {"status": "error", "message": "This proposal type requires manual technician application."}

        # 2. Create rollback snapshot
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"policy_pre_{proposal_id}_{timestamp}.json")
        shutil.copy2(self.policy_file, backup_path)

        # 3. Apply the change to memory and disk
        try:
            with open(self.policy_file, "r") as f:
                data = json.load(f)

            target = prop["target_list"]
            item = prop["proposed_item"]

            # Hygiene: Normalize and Validate Regex before write
            import re
            if target == "forbidden_regex":
                rule_str = item.strip()
                try:
                    re.compile(rule_str)
                except re.error as e:
                    return {"status": "error", "message": f"Malformed regex in proposal: {e}"}
                cleaned_item = rule_str
            elif target == "scrub_patterns":
                pat, placeholder = item
                rule_str = pat.strip()
                try:
                    re.compile(rule_str)
                except re.error as e:
                    return {"status": "error", "message": f"Malformed scrub regex: {e}"}
                cleaned_item = [rule_str, placeholder]
            else:
                return {"status": "error", "message": "Unknown target list."}

            if target not in data:
                data[target] = []
            
            # Additive only check with normalization
            if cleaned_item not in data[target]:
                data[target].append(cleaned_item)
            
            data["version"] = data.get("version", 0) + 1
            data["last_updated"] = datetime.utcnow().isoformat()
            data["last_proposal_id"] = proposal_id

            with open(self.policy_file, "w") as f:
                json.dump(data, f, indent=2)

            # 4. Refresh engine in-memory state
            catalyst_engine._load_patterns()

            # 5. Record signed audit in Ledger
            governance_ledger_engine.record_decision(
                decision_type="CATALYST_POLICY_APPLIED",
                target_ref_type="CATALYST_POLICY",
                target_id=proposal_id,
                actor="CREATOR",
                action_taken="APPLIED",
                rationale=f"Approved hardening refinement for pattern: {prop['pattern_origin']}. {prop['rationale']}",
                evidence_refs={
                    "proposal": prop,
                    "rollback_id": os.path.basename(backup_path),
                    "creator_audit": creator_metadata
                },
                severity_context="LOW"
            )

            return {
                "status": "success",
                "message": f"Refinement {proposal_id} applied successfully.",
                "rollback_id": os.path.basename(backup_path),
                "applied_item": item
            }

        except Exception as e:
            logger.error(f"Catalyst Apply Service: Failed to apply {proposal_id}: {e}")
            # Attempt to restore from backup if we partially failed on write
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.policy_file)
            return {"status": "error", "message": f"Application failed: {str(e)}"}

    def rollback_refinement(self, rollback_id: str) -> Dict[str, Any]:
        """
        Reverts the policy to a previous state using a rollback snapshot.
        """
        # Hygiene: Prevent path traversal
        if ".." in rollback_id or "/" in rollback_id or "\\" in rollback_id:
             return {"status": "error", "message": "Invalid rollback identifier."}

        source_path = os.path.join(self.backup_dir, rollback_id)
        if not os.path.exists(source_path):
            return {"status": "error", "message": "Rollback snapshot not found."}

        try:
            shutil.copy2(source_path, self.policy_file)
            catalyst_engine._load_patterns()

            # Log reversion
            governance_ledger_engine.record_decision(
                decision_type="CATALYST_POLICY_ROLLBACK",
                target_ref_type="CATALYST_POLICY",
                target_id=rollback_id,
                actor="CREATOR",
                action_taken="ROLLED_BACK",
                rationale=f"Governance state reversion to snapshot: {rollback_id}.",
                evidence_refs={"rollback_id": rollback_id},
                severity_context="MODERATE"
            )

            return {"status": "success", "message": f"State restored from {rollback_id}."}
        except Exception as e:
            return {"status": "error", "message": f"Rollback failed: {str(e)}"}

catalyst_apply_service = CatalystApplyService()
