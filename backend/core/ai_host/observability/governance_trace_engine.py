import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class GovernanceActionTrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_id: str
    target_type: str = 'MISSION'
    source_snapshot_id: Optional[str] = None
    
    # Decision
    creator_action: str # ACCEPT_RISK, REBASE, FREEZE, IGNORE, CLOSE_DEBT, ESCALATE
    initial_severity: str
    initial_fused_status: str
    
    # Forensic outcome
    outcome_status: str = 'PENDING_OUTCOME' # EFFECTIVE, PARTIAL_RELIEF, NO_EFFECT, DEGRADED_AFTER_ACTION, PENDING
    current_severity: Optional[str] = None
    severity_delta: float = 0.0
    
    rationale_summary: Optional[str] = None
    confidence: float = 1.0
    applied_at: datetime = Field(default_factory=datetime.now)
    last_evaluated_at: datetime = Field(default_factory=datetime.now)
    next_recommended_action: Optional[str] = None
    
    # Context Aggregation
    target_domain: str = "GLOBAL"
    action_category: str = "TACTICAL"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GovernanceTraceEngine:
    """
    OMNIWEB — BLOQUE: ACTION TRACE & CONSEQUENCE ENGINE.
    Detects creator decisions and evaluates their impact on governance risk.
    """
    
    def register_trace(self, target_id: str, action: str, target_type: str = 'MISSION', domain: str = "GLOBAL") -> GovernanceActionTrace:
        """
        Records a decision taken by the creator based on the latest fusion signal.
        """
        # 1. Fetch Latest Fusion Signal as baseline
        snapshot = self._get_latest_snapshot(target_id)
        
        trace = GovernanceActionTrace(
            target_id=target_id,
            target_type=target_type,
            target_domain=domain,
            source_snapshot_id=snapshot.fusion_id if snapshot else None,
            creator_action=action,
            initial_severity=snapshot.severity_band if snapshot else "LOW",
            initial_fused_status=snapshot.fused_status if snapshot else "NOMINAL"
        )
        
        self._persist_trace(trace)
        
        # Record in Strategic Ledger (PHASE 109 Integration)
        from backend.core.governance.ledger_engine import governance_ledger_engine
        
        # Map creator_action to Strategic Types
        dtype = "STRATEGIC_PIVOT" if action in ["REBASE", "FREEZE", "ESCALATE"] else "RISK_OVERRIDE" if action == "ACCEPT_RISK" else "GOVERNANCE_ACTION"
        
        governance_ledger_engine.record_decision(
            decision_type=dtype,
            target_ref_type=target_type,
            target_id=target_id,
            actor="CREATOR",
            action_taken=action,
            rationale=f"Decisión táctica sobre {target_type} {target_id}. Baseline: {trace.initial_severity}.",
            evidence_refs={"trace_id": trace.trace_id, "snapshot_id": trace.source_snapshot_id},
            severity_context=trace.initial_severity
        )
        
        return trace

    def evaluate_active_traces(self, target_id: Optional[str] = None) -> List[GovernanceActionTrace]:
        """
        Audits pending traces to determine if the decision had the expected effect.
        """
        with db_manager.get_connection() as conn:
            query = "SELECT * FROM governance_action_traces WHERE outcome_status IN ('PENDING_OUTCOME', 'PARTIAL_RELIEF')"
            if target_id:
                query += f" AND target_id = '{target_id}'"
            
            rows = conn.execute(query).fetchall()
            evaluated = []
            
            for row in rows:
                from backend.core.ai_host.observability.governance_fusion_engine import fusion_engine
                trace_data = dict(row)
                # Map SQLite col names to model
                trace = self._map_row_to_trace(trace_data)
                
                # REVALUATE CONSEQUENCE (Pass evaluate_traces=False to avoid RECURSION)
                current_snapshot = fusion_engine.get_fusion_snapshot(trace.target_id, trace.target_type, evaluate_traces=False)
                
                # Logic: Compare initial vs current
                # Severity Bands: LOW(0), MEDIUM(1), HIGH(2), CRITICAL(3)
                severity_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
                initial_val = severity_map.get(trace.initial_severity, 0)
                current_val = severity_map.get(current_snapshot.severity_band, 0)
                delta = current_val - initial_val
                
                outcome = "PENDING_OUTCOME"
                rationale = "Evaluando consecuencia operativa..."
                
                if trace.creator_action == "REBASE":
                    if current_val < initial_val:
                        outcome = "EFFECTIVE"
                        rationale = f"Acción efectiva: Riesgo estructural aliviado ({trace.initial_severity} -> {current_snapshot.severity_band})."
                    elif current_val == initial_val and current_val > 0:
                        outcome = "PARTIAL_RELIEF"
                        rationale = "Rebase parcial; persisten otros vectores de riesgo (Deuda/Presión)."
                    else:
                        outcome = "NO_EFFECT"
                
                elif trace.creator_action == "ACCEPT_RISK":
                    if current_val > initial_val:
                        outcome = "DEGRADED_AFTER_ACTION"
                        rationale = f"Aceptación ineficaz: El riesgo escaló bajo presión ({trace.initial_severity} -> {current_snapshot.severity_band})."
                    elif current_val == initial_val:
                        outcome = "PARTIAL_RELIEF"
                        rationale = "Riesgo aceptado y estable."
                    else:
                        outcome = "EFFECTIVE" # Debt closed or pressure gone
                
                trace.outcome_status = outcome
                trace.current_severity = current_snapshot.severity_band
                trace.severity_delta = float(delta)
                trace.last_evaluated_at = datetime.now()
                
                self._update_trace(trace)
                
                # Sync with Strategic Ledger (PHASE 109)
                from backend.core.governance.ledger_engine import governance_ledger_engine
                ledger_outcome = "EFFECTIVE" if outcome == "EFFECTIVE" else "DEGRADED" if outcome == "DEGRADED_AFTER_ACTION" else "PENDING_OUTCOME"
                governance_ledger_engine.update_outcome(trace.target_id, ledger_outcome)
                
                evaluated.append(trace)
                
        return evaluated

    def get_latest_trace(self, target_id: str) -> Optional[GovernanceActionTrace]:
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM governance_action_traces WHERE target_id = ? ORDER BY applied_at DESC LIMIT 1", (target_id,)).fetchone()
            if row:
                return self._map_row_to_trace(dict(row))
        return None

    def _get_latest_snapshot(self, target_id: str):
        from backend.core.ai_host.observability.governance_fusion_engine import GovernanceFusionSnapshot
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM governance_fusion_snapshots WHERE target_id = ? ORDER BY created_at DESC LIMIT 1", (target_id,)).fetchone()
            if row:
                # Mocking a snapshot model from row
                data = dict(row)
                return GovernanceFusionSnapshot(
                    fusion_id=data["fusion_id"],
                    target_id=data["target_id"],
                    target_type=data["target_type"],
                    fused_status=data["fused_status"],
                    severity_band=data["severity_band"],
                    rationale=data["rationale"],
                    next_action=data["next_action"]
                )
        return None

    def _persist_trace(self, t: GovernanceActionTrace):
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO governance_action_traces (
                    trace_id, target_id, target_type, source_snapshot_id, 
                    creator_action, initial_severity, initial_fused_status,
                    outcome_status, current_severity, rationale_summary,
                    target_domain, action_category, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.trace_id, t.target_id, t.target_type, t.source_snapshot_id,
                t.creator_action, t.initial_severity, t.initial_fused_status,
                t.outcome_status, t.current_severity, t.rationale_summary,
                t.target_domain, t.action_category, json.dumps(t.metadata)
            ))
            conn.commit()

    def _update_trace(self, t: GovernanceActionTrace):
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE governance_action_traces SET 
                    outcome_status = ?, current_severity = ?, severity_delta = ?,
                    rationale_summary = ?, last_evaluated_at = ?, next_recommended_action = ?
                WHERE trace_id = ?
            """, (
                t.outcome_status, t.current_severity, t.severity_delta,
                t.rationale_summary, t.last_evaluated_at.isoformat(), t.next_recommended_action,
                t.trace_id
            ))
            conn.commit()

    def _map_row_to_trace(self, r: Dict[str, Any]) -> GovernanceActionTrace:
        # SQLite dates
        applied = r["applied_at"]
        if isinstance(applied, str): applied = datetime.fromisoformat(applied)
        eval_at = r["last_evaluated_at"]
        if isinstance(eval_at, str): eval_at = datetime.fromisoformat(eval_at)
        
        return GovernanceActionTrace(
            trace_id=r["trace_id"],
            target_id=r["target_id"],
            target_type=r["target_type"],
            source_snapshot_id=r["source_snapshot_id"],
            creator_action=r["creator_action"],
            initial_severity=r["initial_severity"],
            initial_fused_status=r["initial_fused_status"],
            outcome_status=r["outcome_status"],
            current_severity=r["current_severity"],
            severity_delta=r["severity_delta"],
            rationale_summary=r["rationale_summary"],
            applied_at=applied,
            last_evaluated_at=eval_at,
            next_recommended_action=r["next_recommended_action"],
            target_domain=r.get("target_domain", "GLOBAL"),
            action_category=r.get("action_category", "TACTICAL"),
            metadata=json.loads(r.get("metadata", "{}")) if r.get("metadata") else {}
        )

    def get_forensic_dashboard(self) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: FORENSIC DATA AGGREGATION.
        Consolidates action history into a tactical cockpit.
        """
        from backend.core.database import db_manager
        with db_manager.get_connection() as conn:
            # 1. Fetch All Traces
            rows = conn.execute("SELECT * FROM governance_action_traces ORDER BY applied_at DESC").fetchall()
            traces = [self._map_row_to_trace(dict(r)) for r in rows]
            
            # 2. Aggregations
            summary = {
                "total_decisions": len(traces),
                "outcomes": {
                    "EFFECTIVE": 0,
                    "PARTIAL": 0,
                    "DEGRADED": 0,
                    "NO_EFFECT": 0,
                    "PENDING": 0
                },
                "hotspots": {} # Domains with most degradation
            }
            
            for t in traces:
                status = t.outcome_status
                if status == "EFFECTIVE": summary["outcomes"]["EFFECTIVE"] += 1
                elif status == "PARTIAL_RELIEF": summary["outcomes"]["PARTIAL"] += 1
                elif status == "DEGRADED_AFTER_ACTION": summary["outcomes"]["DEGRADED"] += 1
                elif status == "NO_EFFECT": summary["outcomes"]["NO_EFFECT"] += 1
                elif status == "PENDING_OUTCOME": summary["outcomes"]["PENDING"] += 1
                
                # Hotspots
                if status == "DEGRADED_AFTER_ACTION":
                    summary["hotspots"][t.target_domain] = summary["hotspots"].get(t.target_domain, 0) + 1
            
            # 3. Decision Insights (Heuristics)
            insights = []
            if summary["outcomes"]["DEGRADED"] > 3:
                insights.append("ALERTA: Se detecta un patrón de degradación post-intervención en múltiples misiones.")
            
            top_hotspot = None
            if summary["hotspots"]:
                top_hotspot = max(summary["hotspots"], key=summary["hotspots"].get)
                insights.append(f"Fricción Focal: El dominio '{top_hotspot}' concentra la mayor ineficacia táctica.")
            
            return {
                "summary": summary,
                "traces": [t.model_dump() for t in traces],
                "insights": insights
            }

trace_engine = GovernanceTraceEngine()
