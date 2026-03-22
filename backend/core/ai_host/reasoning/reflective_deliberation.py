from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass, field
from datetime import datetime
from .evidence_engine import EvidenceItem, EvidenceBundle, evidence_engine
from .runtime_truth import runtime_truth, TechnicalClaim
from ..cognition.cognitive_core import cognitive_core
from ..learning.adaptive_learning import adaptive_learning

logger = logging.getLogger(__name__)

@dataclass
class ReflectiveAnalysis:
    observation: str
    primary_hypothesis: str
    alternative_hypothesis: str
    confidence_level: float
    missing_evidence: List[str]
    recommended_action: str
    limitations: List[str]

class ReflectiveDeliberation:
    """
    Improves reasoning depth by comparing alternative explanations and reasoning transparently.
    Omni evolves from evidence-based reasoning to reflective analysis.
    """
    
    def __init__(self):
        self.reliability_threshold = 0.7

    async def analyze(self, message: str, bundle: Optional[EvidenceBundle] = None) -> ReflectiveAnalysis:
        """
        Conducts a deep reflective analysis using Cognitive Core, Evidence Engine,
        Adaptive Learning, and Execution History.
        """
        # 1. Ensure we have evidence
        if not bundle:
            bundle = await evidence_engine.collect_evidence()
            
        # 2. Base Claim from Runtime Truth
        claim = runtime_truth.evaluate(bundle, request_msg=message)
        
        # 3. Pull context from Learning & History
        reliability_report = adaptive_learning.get_reliability_report()
        history = cognitive_core.execution_history
        
        # 4. Observation - Grounded in current state
        ws = cognitive_core.world_state
        observation = f"The system is currently in {ws.system_health} state with {len(ws.active_chips)} active chips."
        if claim.supporting_evidence:
            observation += f" Primary anomaly detected in {claim.supporting_evidence[0].key}."
        
        # Apply translations to observation
        observation = observation.replace("Metrics are nominal, but the user reports a localized operational anomaly", "Las métricas parecen nominales, pero se reconoce la anomalía reportada localmente")
        observation = observation.replace("The system is currently in", "El sistema se encuentra en estado")
        
        # 5. Primary Hypothesis
        primary = claim.claim
        
        # 6. Alternative Hypothesis
        alt = self._generate_alternative(bundle, claim, reliability_report)
        
        # 7. Confidence Level (Adjusted by Learning reliability)
        confidence = claim.confidence
        if claim.supporting_evidence:
            source_key = f"{claim.supporting_evidence[0].source}.{claim.supporting_evidence[0].key}"
            reliability = reliability_report["evidence_reliability"].get(source_key, 1.0)
            confidence = round(confidence * reliability, 2)

        # 8. Missing Evidence / Limitations
        missing = claim.limitations or []
        if not bundle.items:
            missing.append("No runtime metrics captured in current bundle")
        if claim.conflict_detected:
            missing.append("Cross-layer metric correlation failure")

        # 9. Recommended Best Next Action
        action = self._determine_next_action(claim, history)
            
        logger.info(f"[REFLECTIVE_DELIBERATION] Deep analysis completed for primary hypothesis: {primary}")
        
        return ReflectiveAnalysis(
            observation=observation,
            primary_hypothesis=primary,
            alternative_hypothesis=alt,
            confidence_level=confidence,
            missing_evidence=missing,
            recommended_action=action,
            limitations=claim.limitations
        )

    def _generate_alternative(self, bundle: EvidenceBundle, claim: TechnicalClaim, learning: Dict[str, Any]) -> str:
        """Generates at least one alternative hypothesis based on learning patterns or technical defaults."""
        patterns = learning.get("top_patterns", {})
        
        # If we have patterns that correlate with failure for the current primary cause
        for metric, stats in patterns.items():
            if metric in claim.claim.lower() and stats.get("weighted_impact", 0) < 0:
                return f"Transient failure in {metric} triggered by historical pattern '{metric}_degradation_loop'."

        # Default alternatives based on technical context
        if "latency" in claim.claim.lower():
            return "Metrical noise or NTP drift causing false positive latency spikes in the bus."
        
        if "nominal" in claim.claim.lower() or claim.is_insufficient:
            return "Silent failure in the message bus prevents error propagation to metrics."
            
        return "Underlying resource contention or OS-level context switching impacting module execution."

    def _determine_next_action(self, claim: TechnicalClaim, history: List[Any]) -> str:
        """Recommends the best next action based on claim and past results."""
        if claim.is_insufficient:
            return "Increase metric sampling priority and check raw module logs."
            
        recent_failures = [h for h in history[-5:] if h.outcome == "FAILED"]
        if len(recent_failures) > 2:
            return "Rollback last mutation and enter Deep Diagnostic Mode."
            
        if claim.confidence < 0.5:
            return "Collect more specific evidence from the affected layer before proceeding with a patch."
            
        return "Initiate Creator Plan for targeted repair of the identified layer."

reflective_deliberation = ReflectiveDeliberation()
