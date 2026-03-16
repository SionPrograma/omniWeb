import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

class OutcomeType(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"

class LearningRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: Optional[str] = None
    evidence_snapshot_id: Optional[str] = None
    plan_id: str
    execution_outcome: str
    success_score: float  # 0.0 to 1.0
    timestamp: datetime = Field(default_factory=datetime.now)

class OutcomeEvaluation(BaseModel):
    outcome_type: OutcomeType
    impact_score: float
    confidence_adjustment: float

class LearningModel(BaseModel):
    hypothesis_accuracy: Dict[str, float] = {}  # hypothesis_type/key -> score
    evidence_reliability: Dict[str, float] = {} # source.key -> score
    execution_success_rate: float = 1.0
    confidence_bias: float = 0.0
    pattern_correlations: Dict[str, Dict[str, float]] = {} # symptom -> {cause: probability}

class AdaptiveLearning:
    """
    Tracks relationship between Hypothesis, Evidence, Plan and Outcome.
    Refines future reasoning based on execution history.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdaptiveLearning, cls).__new__(cls)
            cls._instance.learning_history: List[LearningRecord] = []
            cls._instance.model = LearningModel()
            cls._instance.hypothesis_history: Dict[str, List[bool]] = {} # hypothesis_id -> [successes]
        return cls._instance

    def record_outcome(self, plan_id: str, hypothesis_id: Optional[str], outcome: str, evidence: List[str], evidence_snapshot_id: Optional[str] = None):
        """Main entry point to learn from a completed execution."""
        
        # 1. Evaluate Outcome
        evaluation = self._evaluate_outcome(outcome)
        
        # 2. Create Record
        record = LearningRecord(
            plan_id=plan_id,
            hypothesis_id=hypothesis_id,
            evidence_snapshot_id=evidence_snapshot_id,
            execution_outcome=outcome,
            success_score=evaluation.impact_score
        )
        self.learning_history.append(record)
        
        # 3. Update Calibration and Core Status
        if hypothesis_id:
            self._adjust_hypothesis_calibration(hypothesis_id, evaluation)
        else:
            logger.warning(f"[ADAPTIVE_LEARNING] Execution {plan_id} completed without hypothesis_id (missing_traceability).")
            
        # 4. Update Global Model
        self._update_model_stats(evaluation, evidence)
        
        # 5. Pattern Extraction
        self._extract_patterns(evidence, evaluation)
        
        logger.info(f"[ADAPTIVE_LEARNING] Outcome recorded for plan {plan_id}. Outcome: {outcome} Adjust: {evaluation.confidence_adjustment}")
        return record

    def _evaluate_outcome(self, outcome: str) -> OutcomeEvaluation:
        """Translates raw execution status into learning metrics."""
        if outcome == "COMPLETED":
            return OutcomeEvaluation(
                outcome_type=OutcomeType.SUCCESS,
                impact_score=1.0,
                confidence_adjustment=0.1
            )
        elif outcome == "FAILED":
            return OutcomeEvaluation(
                outcome_type=OutcomeType.FAILURE,
                impact_score=0.0,
                confidence_adjustment=-0.2
            )
        else: # PARTIAL or other
            return OutcomeEvaluation(
                outcome_type=OutcomeType.PARTIAL,
                impact_score=0.5,
                confidence_adjustment=-0.05
            )

    def _adjust_hypothesis_calibration(self, hypothesis_id: str, evaluation: OutcomeEvaluation):
        """Updates the specific reliability score of a hypothesis using CognitiveCore lifecycle rules."""
        from ..cognition.cognitive_core import cognitive_core
        
        # Status Mapping
        status_map = {
            OutcomeType.SUCCESS: "verified",
            OutcomeType.FAILURE: "rejected",
            OutcomeType.PARTIAL: "partial"
        }
        
        target_status = status_map.get(evaluation.outcome_type, "partial")
        
        # Delegate to Core for state change
        cognitive_core.update_hypothesis_status(
            hypothesis_id=hypothesis_id,
            status=target_status,
            confidence_delta=evaluation.confidence_adjustment
        )

    def _update_model_stats(self, evaluation: OutcomeEvaluation, evidence: List[str]):
        """Updates global reliability metrics for evidence sources."""
        for e in evidence:
            source_key = e.split('=')[0] if '=' in e else e
            current = self.model.evidence_reliability.get(source_key, 1.0)
            
            # If evidence led to success, reliability goes up, otherwise down
            if evaluation.outcome_type == OutcomeType.SUCCESS:
                new_val = min(current + 0.05, 1.2) # Allow slight "boost" for highly reliable sources
            elif evaluation.outcome_type == OutcomeType.FAILURE:
                new_val = max(current - 0.1, 0.1)
            else:
                new_val = current
                
            self.model.evidence_reliability[source_key] = round(new_val, 2)

    def _extract_patterns(self, evidence: List[str], evaluation: OutcomeEvaluation):
        """Detects correlations between symptoms (evidence) and success."""
        # Simple pattern: correlation between specific metrics and successful resolutions
        for e in evidence:
            if '=' not in e: continue
            metric, value = e.split('=')[0], e.split('=')[1]
            
            # Focus on technical anomalies as symptoms
            is_anomaly = "latency" in metric or "error" in str(value).lower() or "warning" in str(value).lower()
            
            if is_anomaly:
                if metric not in self.model.pattern_correlations:
                    self.model.pattern_correlations[metric] = {"weighted_impact": 0.0, "occurences": 0}
                
                stats = self.model.pattern_correlations[metric]
                stats["occurences"] += 1
                
                # Weight impact based on success (1.0) or failure (-1.0)
                influence = 1.0 if evaluation.outcome_type == OutcomeType.SUCCESS else -1.0
                stats["weighted_impact"] = round(stats["weighted_impact"] + influence, 2)
                
                logger.info(f"[ADAPTIVE_LEARNING] Pattern updated for {metric}: impact {stats['weighted_impact']}")

    def get_reliability_report(self) -> Dict[str, Any]:
        """Provides statistics for the BrainRouter."""
        return {
            "evidence_reliability": self.model.evidence_reliability,
            "top_patterns": self.model.pattern_correlations
        }

adaptive_learning = AdaptiveLearning()
