import logging
from typing import List, Dict, Any, Optional
from ..learning.adaptive_learning import adaptive_learning

logger = logging.getLogger(__name__)

class AuditLoop:
    """
    Evaluates shadow swarm outputs for errors, inconsistencies, or missing requirements.
    Extracts patterns for the learning layer.
    """
    
    def __init__(self):
        pass

    async def verify(self, job_results: List[Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs a cognitive audit cycle on the results of the swarm execution."""
        logger.info("[AUDIT_LOOP] Verifying swarm outputs against architecture and design principles.")
        
        findings = []
        errors = 0
        architectural_conflicts = 0
        performance_risks = 0
        
        for res in job_results:
            if not res: continue
            if not isinstance(res, dict): continue
            
            # 1. ERROR DETECTION
            if "error" in res:
                errors += 1
                findings.append(f"CRITICAL: Task failure - {res['error']}")
            
            # 2. ARCHITECTURAL ALIGNMENT
            impact = res.get("impact_score", 0.0)
            if impact < 0.5 and "artifact" in res:
                architectural_conflicts += 1
                findings.append(f"CONFLICT: {res['artifact']} deviates from Omni modular patterns.")
            
            # 3. PERFORMANCE RISK SENSING
            if res.get("risk_assessment") == "high":
                performance_risks += 1
                findings.append(f"RISK: Performance degradation detected in {res.get('artifact', 'unknown')}")

        status = "passed"
        if errors > 0: status = "failed"
        elif architectural_conflicts > 0 or performance_risks > 0: status = "flagged"

        audit_result = {
            "status": status,
            "error_count": errors,
            "conflicts": architectural_conflicts,
            "risks": performance_risks,
            "findings": findings,
            "integrity_score": max(0.0, 1.0 - (errors * 0.3) - (architectural_conflicts * 0.1))
        }

        # Sync audit result to learning layer
        adaptive_learning.record_outcome(
            plan_id="swarm_audit",
            hypothesis_id=None,
            outcome="COMPLETED" if status == "passed" else "FAILED",
            evidence=[f"audit.status={status}", f"audit.integrity={audit_result['integrity_score']}"]
        )

        return audit_result

audit_loop = AuditLoop()
