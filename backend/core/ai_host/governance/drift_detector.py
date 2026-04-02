
import logging
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DriftSeverity:
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class DriftType:
    RESTRICTION = "RESTRICTION_DRIFT" # Mutation in forbidden area
    SCOPE = "SCOPE_DRIFT"             # Expanding beyond allowed_paths
    EXTERNAL = "EXTERNAL_DRIFT"       # File changed outside OmniWeb flow
    GOVERNANCE = "GOVERNANCE_DRIFT"   # Rules not being followed

class DriftAlert:
    def __init__(self, type: str, severity: str, message: str, targets: List[str] = [], suggestion: str = ""):
        self.type = type
        self.severity = severity
        self.message = message
        self.targets = targets
        self.suggestion = suggestion
        self.timestamp = datetime.now().isoformat()

class ConstitutionalDriftDetector:
    """
    Silent guardian that ensures the system adheres to the Creator's Constitution.
    """
    def __init__(self, mission_manager=None):
        self.mission_manager = mission_manager
        self.drift_history = []

    def check_drift(self, mission_state: Any) -> List[DriftAlert]:
        """
        Main entry point for a silent audit pass.
        """
        alerts = []
        if not mission_state: return alerts

        params = mission_state.parameters
        
        # 1. Check for Restriction Evasion (Audit recent mutations)
        # (This would normally be triggered by ApprovalGate event accumulation)
        
        # 2. Check for External Drift (File integrity for frozen/forbidden)
        external_drift = self._check_external_drift(params)
        if external_drift: alerts.append(external_drift)

        # 3. Check for Scope Creep
        # (Based on related_targets expansion vs allowed_paths)
        
        return alerts

    def _check_external_drift(self, params: Dict[str, Any]) -> Optional[DriftAlert]:
        """Checks if files in restricted zones changed unexpectedly."""
        frozen = params.get("frozen_paths", [])
        forbidden = params.get("forbidden_paths", [])
        
        flagged_files = []
        # In a real impl, we'd check against a 'last_known_hash' or timestamp
        # For Phase 21, we'll simulate detection of drift if a file is modified 
        # while frozen (mocked for demo purposes).
        
        if flagged_files:
            return DriftAlert(
                type=DriftType.EXTERNAL,
                severity=DriftSeverity.WARNING,
                message=f"Se detectaron cambios externos en zonas restringidas.",
                targets=flagged_files,
                suggestion="Revisar auditoría o restaurar último perfil seguro."
            )
        return None

    def record_drift_event(self, alert: DriftAlert):
        """Registers a drift event in the mission context for UI visibility."""
        if not self.mission_manager:
             try:
                  from backend.core.ai_host.memory.mission_manager import mission_manager
                  self.mission_manager = mission_manager
             except ImportError: return

        mission = self.mission_manager.get_active_mission()
        if not mission: return

        drifts = mission.context_snap.get("drift_alerts", [])
        # Add to snap
        drifts.append({
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "targets": alert.targets,
            "suggestion": alert.suggestion,
            "timestamp": alert.timestamp
        })
        
        # Keep only latest 10
        mission.context_snap["drift_alerts"] = drifts[-10:]
        
        # If critical, elevate to blocked reasons
        if alert.severity == DriftSeverity.CRITICAL:
             mission.blocked_reasons.append(f"ALERTA ROJA - DERIVA CRÍTICA: {alert.message}")
        
        self.mission_manager.save_mission(mission)
        logger.warning(f"[DRIFT_DETECTOR] {alert.severity}: {alert.message} ({alert.type})")

drift_detector = ConstitutionalDriftDetector()
