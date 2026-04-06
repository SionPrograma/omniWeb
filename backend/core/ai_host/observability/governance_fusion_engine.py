import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.ai_host.observability.governance_trace_engine import trace_engine

logger = logging.getLogger(__name__)

class GovernanceFusionSnapshot(BaseModel):
    fusion_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_id: str
    target_type: str
    fused_status: str
    severity_band: str
    rationale: str
    next_action: str
    
    # Traceability
    debt_state: Optional[str] = None
    pressure_state: Optional[str] = None
    advisory_state: Optional[str] = None
    base_compromise_state: Optional[str] = None
    
    # Forensic Consequence Trace
    last_action_trace: Optional[Dict[str, Any]] = None
    
    confidence: float = 1.0
    created_at: datetime = Field(default_factory=datetime.now)

class GovernanceFusionEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE PRESSURE + DEBT FUSION ENGINE.
    Unified risk logic that integrates Debt Lifecycle, Pressure Trajectory, 
    and Advisory Overlap into a single operational status.
    """
    
    def get_fusion_snapshot(self, target_id: str, target_type: str = 'MISSION', evaluate_traces: bool = True) -> GovernanceFusionSnapshot:
        """
        Calculates and persists a composite governance state for a mission or domain.
        """
        # 1. Fetch Debt Data
        # Reusing branch_manager governance audit
        overrides = branch_manager.get_risk_overrides()
        target_ov = next((o for o in overrides if o.target_id == target_id), None)
        debt_state = target_ov.debt_state if target_ov else "NONE"
        risk_level = target_ov.risk_level if target_ov else "LOW"
        
        # 2. Fetch Pressure Data
        timeline = branch_manager.get_pressure_timeline(target_id)
        pressure_state = timeline.trajectory
        
        # 3. Fetch Advisory Data (Overlap check)
        recs = branch_manager.get_mission_rebase_recommendations()
        target_rec = next((r for r in recs if r["affected_handoff_id"] == target_id), None)
        advisory_state = target_rec.get("risk_level", "NONE") if target_rec else "NONE"
        
        # 4. Fusion Logic (Decision Tree)
        fused_status = "NOMINAL"
        severity_band = "LOW"
        rationale = "Operación bajo parámetros nominales."
        next_action = "CONTINUAR"
        
        # Flags
        is_overdue = debt_state in ["OVERDUE", "DEGRADED"]
        is_review_due = debt_state == "REVIEW_DUE"
        
        # Pressure flags (Direct check on peak risk detected)
        peak_risk = "LOW"
        if timeline and timeline.events:
            peak_risk = max([e.risk_level for e in timeline.events], key=lambda x: {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}.get(x, 0))
        
        is_high_pressure = pressure_state in ["ESCALATING_PRESSURE", "IGNORED_AND_DEGRADED", "PERSISTENT_PRESSURE"] or peak_risk in ["HIGH", "CRITICAL"]
        is_critical_pressure = peak_risk == "CRITICAL"
        is_critical_adv = advisory_state in ["HIGH", "CRITICAL"]
        
        # Composite Priorities
        if is_overdue and is_high_pressure and is_critical_adv:
            fused_status = "STRUCTURALLY_COMPROMISED"
            severity_band = "CRITICAL"
            rationale = f"Convergencia crítica detectada: Deuda técnica {debt_state}, presión escalada y base técnica comprometida por advisory {advisory_state}."
            next_action = "FREEZE_UNTIL_RECOVERY"
        elif is_overdue or (is_review_due and is_high_pressure):
            fused_status = "IMMEDIATE_REVIEW_REQUIRED"
            severity_band = "HIGH"
            rationale = f"Se requiere revisión urgente. La deuda ha expirado o se ha degradado bajo presión persistente."
            next_action = "OPEN_DEBT_COCKPIT"
        elif is_critical_adv:
            fused_status = "PRESSURED_AND_DEGRADED"
            severity_band = "HIGH"
            rationale = "La misión opera sobre un dominio con advisories críticas pendientes de rebase."
            next_action = "OPEN_REBASE_PREVIEW"
        elif is_high_pressure:
            fused_status = "WATCH_ESCALATION"
            severity_band = "HIGH" if is_critical_pressure else "MEDIUM"
            rationale = "Detección de presión de gobernanza atípica o escalada sobre este objetivo."
            next_action = "INSPECT_TIMELINE"
        elif debt_state != "NONE" and debt_state != "CLOSED":
            fused_status = "UNDER_ACCEPTED_DEBT"
            severity_band = "MEDIUM"
            rationale = "Operación con deuda técnica aceptada y monitoreada."
            next_action = "REMAIN_CAPABLE"
        elif pressure_state != "NO_PRESSURE" and pressure_state != "TEMPORARY_ALERT":
            fused_status = "WATCH"
            severity_band = "LOW"
            rationale = "Presión de gobernanza leve detectada. Dominio en observación."
            next_action = "CONTINUE_WITH_CAUTION"

        # 5. Fetch Consequence Trace (Result of previous action)
        if evaluate_traces:
            trace_engine.evaluate_active_traces(target_id) # Self-repair/Update
        
        latest_trace = trace_engine.get_latest_trace(target_id)

        snapshot = GovernanceFusionSnapshot(
            target_id=target_id,
            target_type=target_type,
            fused_status=fused_status,
            severity_band=severity_band,
            rationale=rationale,
            next_action=next_action,
            debt_state=debt_state,
            pressure_state=pressure_state,
            advisory_state=advisory_state,
            base_compromise_state="CRITICAL" if is_critical_adv else "STABLE",
            last_action_trace=latest_trace.model_dump() if latest_trace else None
        )
        
        # Traceability persistence
        self._save_to_db(snapshot)
        return snapshot

    def _save_to_db(self, s: GovernanceFusionSnapshot):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO governance_fusion_snapshots (
                        fusion_id, target_id, target_type, fused_status, severity_band,
                        rationale, next_action, debt_state, pressure_state,
                        advisory_state, base_compromise_state, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    s.fusion_id, s.target_id, s.target_type, s.fused_status, s.severity_band,
                    s.rationale, s.next_action, s.debt_state, s.pressure_state,
                    s.advisory_state, s.base_compromise_state, s.confidence
                ))
                conn.commit()

fusion_engine = GovernanceFusionEngine()
