import logging
from typing import Optional, Dict, Any
from .audit_models import AuditResult
from . import contamination_rules as rules

logger = logging.getLogger(__name__)

class CognitiveAuditor:
    """
    Observer & Analyzer for Omni's cognitive integrity.
    V1: Rules-based detection of contract violations and layer contamination.
    """

    def audit_response(
        self,
        response_text: str,
        intent_group: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditResult:
        
        # Initialize result
        result = AuditResult(
            passed=True,
            intent_group=intent_group,
            severity="low",
            raw_response=response_text,
            confidence=0.9 # Base confidence in rules
        )

        lang = metadata.get("lang", "es") if metadata else "es"
        
        # 1. EVASION DETECTION
        evasions = rules.check_evasion(response_text)
        if evasions:
            result.passed = False
            result.failure_types.append("evasion_detected")
            result.severity = "medium"
            result.explanation += f"Detected evasive language: {', '.join(evasions)}. "
            result.suspicious_layers.append("naturalization_layer")
            result.suspicious_modules.append("cognitive_orchestrator")

        # 2. COGNITIVE CONTRACT VALIDATION
        if intent_group.startswith("COGNITIVE"):
            contract = rules.check_cognitive_contract(response_text, lang)
            
            # For COGNITIVE_COMMITMENT, we need Decision + Discard + Reason
            if intent_group == "COGNITIVE_COMMITMENT":
                if not contract["has_decision"]:
                    result.passed = False
                    result.failure_types.append("missing_decision")
                    result.explanation += "Missing explicit decision/choice. "
                if not contract["has_discard"]:
                    result.passed = False
                    result.failure_types.append("missing_rejection")
                    result.explanation += "Missing explicit rejection/sacrifice of alternative. "
                if not contract["has_reason"]:
                    result.passed = False
                    result.failure_types.append("missing_reason")
                    result.explanation += "Missing technical reasoning/impact explanation. "
            
            # For general COGNITIVE, check for at least Diagnostic or Action
            elif not (contract["has_diagnostic"] or contract["has_action"] or contract["has_decision"]):
                result.passed = False
                result.failure_types.append("weak_cognitive_output")
                result.explanation += "Output lacks diagnostic depth or actionable decision. "

        # 3. LANGUAGE CONTAMINATION
        if rules.detect_mixed_language(response_text):
            result.passed = False
            result.failure_types.append("mixed_language_detected")
            result.explanation += "Detected significant mixing of Spanish and English. "
            if result.severity != "critical": result.severity = "medium"

        # 4. NARRATIVE RESIDUE
        if rules.detect_narrative_residue(response_text):
            result.passed = False
            result.failure_types.append("appended_narrative_residue")
            result.explanation += "Detected conversational filler at the end of output. "
            result.suspicious_layers.append("interaction_fallback")

        # 5. FINAL SEVERITY & RECOMMENDATION
        if not result.passed:
            if "evasion_detected" in result.failure_types and intent_group.startswith("COGNITIVE"):
                result.severity = "high"
                result.recommended_action = "Force immediate commitment reload or investigate naturalization bypass."
                result.recommended_tool = "antigravity"
            else:
                result.recommended_action = "Review output alignment with Creator Mode."
                result.recommended_tool = "creator_mode"
        else:
            result.recommended_action = "No action required. Output follows contract."
            result.recommended_tool = "no_action"

        logger.info(f"[COGNITIVE_AUDIT] Result: {result.passed} | Failures: {result.failure_types}")
        return result

# Singleton instance
cognitive_auditor = CognitiveAuditor()
