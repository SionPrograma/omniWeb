"""
Evaluation Ledger — OMNI_PATCH Phase H.
Persistently records capability outcomes for governance and optimization.
"""

import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
from backend.core.ai_host.memory.mission_telemetry import mission_telemetry

logger = logging.getLogger(__name__)

@dataclass
class EvaluationEntry:
    mission_id: str
    provider: str
    model_name: str
    capability_type: str
    success: bool
    tests_passed: bool
    creator_approved: bool
    notes: str = ""
    latency_ms: Optional[float] = None

class EvaluationLedger:
    """
    Surgical recording layer for capability results.
    """

    def record(self, entry: EvaluationEntry) -> None:
        """Records an evaluation entry to telemetry and logs."""
        entry_dict = asdict(entry)
        logger.info(f"[EVALUATION_LEDGER] Recording outcome for {entry.capability_type}: success={entry.success}")
        
        # Integrate with real Mission Telemetry
        mission_telemetry.record_event(
            mission_id=entry.mission_id,
            event_type="CAPABILITY_EVALUATION",
            message=f"Evaluation for {entry.model_name} ({entry.capability_type}) recorded.",
            severity="INFO" if entry.success else "WARNING",
            details=entry_dict,
            source_actor="CreatorLedger"
        )

    def get_mission_history(self, mission_id: str) -> List[Dict[str, Any]]:
        """Retrieves history for a mission from telemetry."""
        events = mission_telemetry.get_recent_events(mission_id)
        return [e.details for e in events if e.event_type == "CAPABILITY_EVALUATION"]

evaluation_ledger = EvaluationLedger()
