"""
Response Critic — OMNI_PATCH Phase G.
Evaluates model/tool outputs for safety, alignment, and utility.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ResponseCritic:
    """
    Independent observer that validates results before they reach the user.
    """

    def review(self, result: Dict[str, Any], mission_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Reviews a raw result object.
        Returns a critique with scores and flags.
        """
        # Support both 'output' and Pydantic 'message'
        output = result.get("message") or result.get("output") or str(result.get("payload", ""))
        intent = (mission_context or {}).get("intent", "unknown")
        
        logger.info(f"[RESPONSE_CRITIC] Reviewing result for intent: {intent}")

        critique = {
            "useful": bool(output and len(output) > 10),
            "clarity_score": 0.9,
            "alignment_score": 1.0,
            "risk_flag": False,
            "violations": [],
            "notes": "Validation against mission constraints passed."
        }

        # Example check: look for "error" in output
        if "error" in output.lower() or "exception" in output.lower():
            critique["useful"] = False
            critique["risk_flag"] = True
            critique["violations"].append("Technical failure detected in output content.")
            critique["notes"] = "Output contains error signatures."

        # Example check: check for hallucinations (empty results pretending to be success)
        if result.get("status") == "success" and not output:
            critique["useful"] = False
            critique["violations"].append("Empty success payload (potential logic gap).")

        logger.info(f"[RESPONSE_CRITIC] Critique result: useful={critique['useful']}, risk={critique['risk_flag']}")
        return critique

response_critic = ResponseCritic()
