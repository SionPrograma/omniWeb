import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class CatalystPolicyReviewer:
    """
    OMNIWEB — BLOQUE: OMNI_CATALYST_V0.5.
    Guided review layer for rejected catalyst pattern analysis.
    Identifies recurring hazards or false positives for Creator review.
    """
    
    def __init__(self):
        self.threshold = 3 # Min occurrences to form a proposal (Default)
        self.lookback_days = 7
        self._load_params()

    def _load_params(self):
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    res = conn.execute("SELECT current_value FROM governance_engine_parameters WHERE param_key = 'PULSE_THRESHOLD'").fetchone()
                    if res:
                        self.threshold = int(res["current_value"])
            except Exception:
                pass

    def get_refinement_proposals(self) -> List[Dict[str, Any]]:
        """
        Analyzes the ledger for rejection patterns and builds proposals.
        """
        self._load_params()
        proposals = []
        try:
            with db_manager.get_connection() as conn:
                # 1. Fetch policy rejections within window
                rejections = conn.execute("""
                    SELECT evidence_refs, created_at, target_id
                    FROM governance_decision_ledger
                    WHERE decision_type IN ('CATALYST_POLICY_REJECT', 'CATALYST_CONTRACT_REJECT')
                      AND created_at > ?
                """, ((datetime.utcnow() - timedelta(days=self.lookback_days)).isoformat(),)).fetchall()

                # 2. Cluster by pattern
                clusters = {}
                for r in rejections:
                    try:
                        refs = json.loads(r["evidence_refs"])
                        pattern = refs.get("pattern", "unknown_fault")
                        if pattern not in clusters:
                            clusters[pattern] = []
                        clusters[pattern].append({
                            "trace_id": r["target_id"],
                            "timestamp": r["created_at"],
                            "sample": refs.get("raw", "")[:200]
                        })
                    except:
                        continue

                # 3. Build proposals based on frequency
                for pattern, occurrences in clusters.items():
                    count = len(occurrences)
                    if count >= self.threshold:
                        proposals.append(self._form_proposal(pattern, occurrences))
                    elif count > 0:
                        # Optional: track minor anomalies without full proposal
                        pass

        except Exception as e:
            logger.error(f"Policy Reviewer: Failed to generate proposals: {e}")
            
        return proposals

    def _form_proposal(self, pattern: str, occurrences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Structures a proposal for the Governance UI.
        """
        count = len(occurrences)
        
        # Determine intent and suggested rule based on pattern type
        if "policy" in pattern or any(x in pattern for x in ["sudo", "chmod", "exec", "eval"]):
            p_type = "POLICY_HARDENING_SUGGESTED"
            proposed_item = pattern # Suggest the pattern itself for deny list
            target_list = "forbidden_regex"
            rationale = f"Recurring block of pattern '{pattern}' detected ({count} times). Suggest adding a more specific structural rule to avoid catalyst drift."
        elif "schema" in pattern or "malformed" in pattern:
            p_type = "CATALYST_PROTOCOL_REVIEW"
            proposed_item = None # Requires manual protocol fix
            target_list = None
            rationale = f"Catalyst is consistently producing malformed outputs relative to pattern '{pattern}'. Interface contract may be drifting."
        elif "path" in pattern or "uuid" in pattern or "/" in pattern or "\\" in pattern:
             p_type = "SCRUB_PATTERN_REFINEMENT"
             # Suggest a generic regex for this specific value if it's a raw path
             if "\\" in pattern or "/" in pattern:
                 proposed_item = [pattern, "[PROTECTED_PATH_REFINED]"]
             else:
                 proposed_item = [pattern, "[PROTECTED_VAL]"]
             target_list = "scrub_patterns"
             rationale = f"Sensitive pattern '{pattern}' leaked into catalyst context. Suggest adding dynamic scrub rule."
        else:
            p_type = "FLUID_PATTERN_AUDIT"
            proposed_item = None
            target_list = None
            rationale = f"Anomalous rejection pattern detected: {pattern}. Review needed to distinguish between drift and false positives."

        return {
            "proposal_id": f"PROP-{datetime.utcnow().strftime('%m%d')}-{pattern[:8].upper()}",
            "type": p_type,
            "pattern_origin": pattern,
            "target_list": target_list,
            "proposed_item": proposed_item,
            "occurrence_count": count,
            "rationale": rationale,
            "evidence_samples": occurrences[:self.threshold],
            "confidence": "HIGH" if count > 5 else "MEDIUM",
            "is_apply_safe": proposed_item is not None,
            "created_at": datetime.utcnow().isoformat()
        }

    def get_proposal_diff(self, proposal_id: str) -> Dict[str, Any]:
        """
        Generates a diff preview for a given proposal.
        """
        proposals = self.get_refinement_proposals()
        prop = next((p for p in proposals if p["proposal_id"] == proposal_id), None)
        if not prop or not prop["is_apply_safe"]:
            return {"error": "Proposal not found or not automatable."}

        from backend.core.governance.catalyst_engine import catalyst_engine
        engine = catalyst_engine
        
        target = prop["target_list"]
        proposed = prop["proposed_item"]
        
        if target == "forbidden_regex":
            current = list(engine.forbidden_regex)
            new = current + [proposed]
        elif target == "scrub_patterns":
            current = [list(p) for p in engine.scrub_patterns]
            new = current + [proposed]
        else:
            return {"error": "Unknown target list."}

        return {
            "proposal_id": proposal_id,
            "target": target,
            "current": current,
            "proposed": new,
            "diff_item": proposed
        }

catalyst_policy_reviewer = CatalystPolicyReviewer()
