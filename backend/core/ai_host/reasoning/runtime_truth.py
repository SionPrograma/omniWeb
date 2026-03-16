from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .evidence_engine import EvidenceItem, EvidenceBundle

@dataclass
class TechnicalClaim:
    claim: str
    supporting_evidence: List[EvidenceItem] = field(default_factory=list)
    confidence: float = 0.0
    limitations: List[str] = field(default_factory=list)
    is_insufficient: bool = False
    conflict_detected: bool = False
    hypothesis_id: Optional[str] = None

class RuntimeTruthEvaluator:
    """
    Evaluates evidence sufficiency and builds grounded technical claims.
    Prevents the AI from hallucinating technical causes without data.
    """
    def evaluate(self, bundle: EvidenceBundle, request_type: str = "technical") -> TechnicalClaim:
        if not bundle.has_sufficient_evidence:
            return TechnicalClaim(
                claim="Insufficient runtime data to support a concrete claim.",
                confidence=0.1,
                limitations=[bundle.uncertainty_reason or "No supporting metrics found."],
                is_insufficient=True
            )

        # 1. Identify critical metrics
        anomalies = [i for i in bundle.items if "warning" in str(i.value).lower() or "error" in str(i.value).lower()]
        latencies = [i for i in bundle.items if "latency" in i.key and isinstance(i.value, (int, float)) and i.value > 40]
        
        # 2. Check for conflicts
        # Example: system_state is WARNING but all chip latencies and healths are nominal
        has_overall_warning = any(i.key == "health" and "warning" in str(i.value).lower() for i in bundle.items)
        has_specific_culprit = len(anomalies) > 0 or len(latencies) > 0
        
        conflict = False
        if has_overall_warning and not has_specific_culprit:
            conflict = True # Conflict between overall status and lack of specific metrics

        # 3. Build Claim
        supporting = []
        claim = ""
        confidence = 0.5
        limitations = []

        if not has_specific_culprit:
            if has_overall_warning:
                claim = "The system reports a non-nominal state, but specific metrics do not yet isolate the root cause."
                confidence = 0.3
            else:
                claim = "The system appears to be operating within normal technical parameters."
                confidence = 0.9
        else:
            # We have culprits
            confidence = 0.6
            if latencies:
                worst = max(latencies, key=lambda x: x.value)
                claim = f"Detected performance degradation likely centered in {worst.key}."
                supporting.append(worst)
                confidence += 0.2
            
            if anomalies:
                for a in anomalies:
                    if a not in supporting:
                        supporting.append(a)
                if not claim:
                    claim = f"System anomalies detected in {', '.join([a.key for a in anomalies])}."
                confidence += 0.1

        # Clip confidence
        confidence = min(max(confidence, 0.0), 1.0)

        claim_obj = TechnicalClaim(
            claim=claim,
            supporting_evidence=supporting,
            confidence=round(confidence, 2),
            limitations=limitations,
            conflict_detected=conflict
        )

        # --- STAGE 11: Register Hypothesis in Cognitive Core ---
        try:
            from ..cognition.cognitive_core import cognitive_core
            h_id = cognitive_core.register_hypothesis(
                description=claim_obj.claim,
                supporting_evidence=[f"{i.source}.{i.key}={i.value}" for i in claim_obj.supporting_evidence],
                confidence=claim_obj.confidence,
                status="active"
            )
            claim_obj.hypothesis_id = h_id
        except Exception as e:
            # We don't want to crash reasoning if cognitive core fail
            pass

        return claim_obj

runtime_truth = RuntimeTruthEvaluator()
