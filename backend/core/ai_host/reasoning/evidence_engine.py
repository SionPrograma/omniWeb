import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class EvidenceItem:
    source: str
    key: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0

    def to_dict(self):
        return {
            "source": self.source,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "confidence": self.confidence
        }

    def dict(self):
        return self.to_dict()
    
    def model_dump(self):
        return self.to_dict()

@dataclass
class EvidenceBundle:
    items: List[EvidenceItem] = field(default_factory=list)
    summary: str = ""
    has_sufficient_evidence: bool = False
    uncertainty_reason: Optional[str] = None
    snapshot_id: Optional[str] = None

    def to_dict(self):
        return {
            "items": [i.to_dict() for i in self.items],
            "summary": self.summary,
            "has_sufficient_evidence": self.has_sufficient_evidence,
            "uncertainty_reason": self.uncertainty_reason,
            "snapshot_id": self.snapshot_id
        }

    def dict(self):
        return self.to_dict()
    
    def model_dump(self):
        return self.to_dict()

class EvidenceEngine:
    """
    Collects concrete technical evidence from the runtime subsystems.
    Ensures that AI reasoning is grounded in actual metrics.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def collect_evidence(self) -> EvidenceBundle:
        bundle = EvidenceBundle()
        
        # 1. System State Evidence
        try:
            from backend.core.permissions import set_chip_context
            from backend.core.system_state.engine import state_engine
            
            with set_chip_context("core"):
                state = await state_engine.get_state()
            
            if state:
                bundle.items.append(EvidenceItem("system_state", "health", state.health.value))
                bundle.items.append(EvidenceItem("system_state", "is_healing", state.is_healing))
                bundle.items.append(EvidenceItem("system_state", "pending_fixes", state.pending_fixes))
                
                if state.memory_usage:
                    bundle.items.append(EvidenceItem("system_state", "memory_percent", state.memory_usage.get("percent")))
                
                # Flow data metrics (Actual technical evidence)
                if state.flow_data:
                    for flow, data in state.flow_data.items():
                        bundle.items.append(EvidenceItem("system_state", f"flow.{flow}.latency", data.get("latency")))
                        # We only add detailed health if it's not normal to highlight issues
                        f_health = str(data.get("health"))
                        if "healthy" not in f_health.lower():
                            bundle.items.append(EvidenceItem("system_state", f"flow.{flow}.health", f_health))
        except Exception as e:
            self.logger.error(f"Evidence Engine: Failed to collect system state: {e}")

        # 2. Chip Orchestrator Evidence
        try:
            from backend.core.chips.chip_orchestrator import chip_orchestrator
            chip_statuses = chip_orchestrator.get_all_chips_status()
            for chip in chip_statuses:
                chip_id = chip["chip_id"]
                status = chip["status"]
                health = chip["health"]
                
                # Focus on non-idle/non-healthy for evidence
                if status != "IDLE" or health != "healthy":
                    bundle.items.append(EvidenceItem("chip_orchestrator", f"chip.{chip_id}.status", status))
                    bundle.items.append(EvidenceItem("chip_orchestrator", f"chip.{chip_id}.health", health))
        except Exception as e:
            self.logger.error(f"Evidence Engine: Failed to collect chip orchestrator state: {e}")

        if not bundle.items:
            bundle.has_sufficient_evidence = False
            bundle.uncertainty_reason = "No runtime metrics or anomalies detected in current snapshot."
        else:
            # Check if we only have boilerplate "healthy" data
            technical_metrics = [i for i in bundle.items if "latency" in i.key or "memory" in i.key]
            anomalies = [i for i in bundle.items if "warning" in str(i.value).lower() or "error" in str(i.value).lower()]
            
            if not technical_metrics and not anomalies:
                bundle.has_sufficient_evidence = False
                bundle.uncertainty_reason = "No specific technical metrics or anomalies found to support a deep diagnosis."
            else:
                bundle.has_sufficient_evidence = True
        
        # --- STAGE 11: Push to Cognitive Core ---
        try:
            from ..cognition.cognitive_core import cognitive_core
            items_dict = [item.to_dict() for item in bundle.items]
            snapshot_id = cognitive_core.push_evidence_bundle({
                "items": items_dict,
                "summary": bundle.summary,
                "has_sufficient_evidence": bundle.has_sufficient_evidence
            })
            bundle.snapshot_id = snapshot_id
        except Exception as e:
            self.logger.error(f"Evidence Engine: Failed to push to Cognitive Core: {e}")
            
        return bundle

evidence_engine = EvidenceEngine()
