import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class WorldState(BaseModel):
    system_health: str = "HEALTHY"
    active_chips: List[str] = []
    flow_metrics: Dict[str, Any] = {}
    runtime_snapshot_timestamp: datetime = Field(default_factory=datetime.now)

class HypothesisRegistry(BaseModel):
    hypothesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    supporting_evidence: List[str]
    confidence: float
    status: str = "active"  # active / rejected / verified
    source: Optional[str] = None
    snapshot_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ExecutionHistory(BaseModel):
    plan_id: str
    steps: List[Dict[str, Any]]
    outcome: str
    evidence_used: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

class LearningRecord(BaseModel):
    pattern: str
    context: str
    reliability: float
    timestamp: datetime = Field(default_factory=datetime.now)

class MissionReasoningRecord(BaseModel):
    creator_command: str
    interpreted_goal: str
    generated_plan: Dict[str, Any]
    audit_findings: List[str]
    execution_outcome: str
    timestamp: datetime = Field(default_factory=datetime.now)

class CognitiveCore:
    """
    Unified "world model" shared by Omni Brain, Creator Copilot, Chips, and Execution Controller.
    Centralizes system state, evidence snapshots, active hypotheses, and execution history.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CognitiveCore, cls).__new__(cls)
            cls._instance.world_state = WorldState()
            cls._instance.hypotheses: Dict[str, HypothesisRegistry] = {}
            cls._instance.execution_history: List[ExecutionHistory] = []
            cls._instance.evidence_snapshots: List[Dict[str, Any]] = []
            cls._instance.learning_records: List[LearningRecord] = []
            cls._instance.mission_history: List[MissionReasoningRecord] = []
        return cls._instance

    def update_world_state(self, system_health: Optional[str] = None, active_chips: Optional[List[str]] = None, flow_metrics: Optional[Dict[str, Any]] = None):
        """Updates the shared world state metrics."""
        if system_health:
            self.world_state.system_health = system_health
        if active_chips is not None:
            self.world_state.active_chips = active_chips
        if flow_metrics:
            self.world_state.flow_metrics.update(flow_metrics)
        
        self.world_state.runtime_snapshot_timestamp = datetime.now()
        logger.info(f"[COGNITIVE_CORE] World state updated: {self.world_state.system_health}")

    def add_learning_record(self, pattern: str, context: str, reliability: float):
        """Stores a validated learning pattern extracted by Shadow agents."""
        record = LearningRecord(pattern=pattern, context=context, reliability=reliability)
        self.learning_records.append(record)
        logger.info(f"[COGNITIVE_CORE] New knowledge reinforced: {pattern}")

    def add_mission_record(self, command: str, goal: str, plan: Dict[str, Any], audit: List[str], outcome: str):
        """Records a high-level creator mission for structural learning."""
        record = MissionReasoningRecord(
            creator_command=command,
            interpreted_goal=goal,
            generated_plan=plan,
            audit_findings=audit,
            execution_outcome=outcome
        )
        self.mission_history.append(record)
        logger.info(f"[COGNITIVE_CORE] Mission Reasoning Record stored: {goal} ({outcome})")

    def get_recent_topic(self) -> Optional[str]:
        """Infers the most recent topic from execution history or hypotheses."""
        if not self.execution_history:
            if self.hypotheses:
                latest_h = list(self.hypotheses.values())[-1]
                return latest_h.description
            return None
        return self.execution_history[-1].plan_id

    def register_hypothesis(self, description: str, supporting_evidence: List[str], confidence: float, status: str = "active"):
        """Registers or updates a reasoning hypothesis."""
        hypothesis = HypothesisRegistry(
            description=description,
            supporting_evidence=supporting_evidence,
            confidence=confidence,
            status=status
        )
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis
        logger.info(f"[COGNITIVE_CORE] Hypothesis registered: {description} (Confidence: {confidence})")
        return hypothesis.hypothesis_id

    def push_evidence_bundle(self, bundle_data: Dict[str, Any]):
        """Stores a snapshot of evidence for traceability."""
        snapshot = {
            "snapshot_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "data": bundle_data
        }
        self.evidence_snapshots.append(snapshot)
        
        # Also update flow metrics if present in bundle
        flow_metrics = {}
        for item in bundle_data.get("items", []):
            if "flow." in item.get("key", ""):
                flow_metrics[item["key"]] = item["value"]
        
        if flow_metrics:
            self.update_world_state(flow_metrics=flow_metrics)
            
        # Keep manageable size
        if len(self.evidence_snapshots) > 50:
            self.evidence_snapshots.pop(0)
            
        return snapshot["snapshot_id"]

    def record_execution_outcome(self, plan_id: str, steps: List[Dict[str, Any]], outcome: str, evidence_used: List[str]):
        """Logs the result of an execution plan."""
        history = ExecutionHistory(
            plan_id=plan_id,
            steps=steps,
            outcome=outcome,
            evidence_used=evidence_used
        )
        self.execution_history.append(history)
        logger.info(f"[COGNITIVE_CORE] Execution recorded for plan {plan_id}: {outcome}")

    def get_active_hypotheses(self) -> List[HypothesisRegistry]:
        """Returns all hypotheses currently marked as active."""
        return [h for h in self.hypotheses.values() if h.status == "active"]

    def update_hypothesis_status(self, hypothesis_id: str, status: str, confidence_delta: float):
        """Updates status and recalibrates confidence based on execution outcomes."""
        if hypothesis_id in self.hypotheses:
            h = self.hypotheses[hypothesis_id]
            h.status = status
            old_conf = h.confidence
            h.confidence = round(min(max(h.confidence + confidence_delta, 0.0), 1.0), 2)
            logger.info(f"[COGNITIVE_CORE] Hypothesis {hypothesis_id} transition: {status} (Conf: {old_conf} -> {h.confidence})")
            return h
        return None

    def get_latest_world_model(self) -> Dict[str, Any]:
        """Returns a combined view of the current world model."""
        return {
            "world_state": self.world_state.dict(),
            "active_hypotheses": [h.dict() for h in self.get_active_hypotheses()],
            "latest_evidence": self.evidence_snapshots[-1] if self.evidence_snapshots else None
        }

cognitive_core = CognitiveCore()
