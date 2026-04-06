import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class HeatmapNode(BaseModel):
    domain: str
    friction_score: float
    severity_band: str  # COOL, WATCH, HOT, CRITICAL, IMPROVING
    rationale: str
    signals: Dict[str, Any] # counts of debt, pressure, etc
    recommended_action: str
    last_updated: str
    audit_status: Optional[str] = None # PENDING_AUDIT, UNDER_AUDIT, etc

class GovernanceHeatmapEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE FRICTION HEATMAP ENGINE.
    Aggregates multi-dimensional signals from Debt, Pressure, Advisory, and Forensic layers
    to generate a spatial friction score per domain.
    """
    
    def get_friction_heatmap(self, skip_evaluation: bool = False) -> List[HeatmapNode]:
        """
        Calculates friction nodes for all domains with active or historical governance footprint.
        """
        nodes = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # 1. Identify all unique domains in the system footprint
                    domains = set()
                    
                    try:
                        trace_rows = conn.execute("SELECT DISTINCT target_domain FROM governance_action_traces WHERE target_domain IS NOT NULL").fetchall()
                        for r in trace_rows: domains.add(r["target_domain"])
                    except: pass
                    
                    try:
                        debt_rows = conn.execute("SELECT DISTINCT affected_domain FROM governance_risk_overrides WHERE affected_domain IS NOT NULL").fetchall()
                        for r in debt_rows: domains.add(r["affected_domain"])
                    except: pass
                    
                    try:
                        adv_rows = conn.execute("SELECT DISTINCT affected_domain FROM governance_rebase_recommendations WHERE affected_domain IS NOT NULL").fetchall()
                        for r in adv_rows: domains.add(r["affected_domain"])
                    except: pass
                    
                    # Also domains under relief
                    try:
                        relief_rows = conn.execute("SELECT DISTINCT source_heatmap_node FROM governance_relief_proposals").fetchall()
                        for r in relief_rows: domains.add(r["source_heatmap_node"])
                    except: pass

                    if not domains: domains = {"Global"}

                    # Phase 1: Calculate raw nodes
                    for domain in domains:
                        nodes.append(self._calculate_domain_node(conn, domain))
                    
                    # Phase 2: Trigger resistance evaluation if not skipped
                    if not skip_evaluation:
                        current_scores = {n.domain: n.friction_score for n in nodes}
                        from .governance_resistance_engine import resistance_engine
                        resistance_engine.evaluate_all_active_reliefs(current_scores=current_scores)
                        
                        # Refresh nodes to pick up new outcomes (RESISTANT band, etc)
                        for i, node in enumerate(nodes):
                            nodes[i] = self._calculate_domain_node(conn, node.domain)
                    
                    # Phase 3: Fetch Root Cause Audit status
                    from .governance_audit_trigger_engine import audit_trigger_engine
                    audit_proposals = audit_trigger_engine.get_proposals()
                    audit_map = {a.source_heatmap_node: a.status for a in audit_proposals}
                    trigger_map = {a.source_heatmap_node: a.trigger_state for a in audit_proposals}

                    for node in nodes:
                        # Apply Audit Visibility logic
                        status = audit_map.get(node.domain)
                        trigger = trigger_map.get(node.domain)
                        
                        if status == "ACCEPTED":
                            node.audit_status = "UNDER_FORENSIC_AUDIT"
                            node.recommended_action = "DEEP_FORENSIC_INVESTIGATION"
                        elif status == "PENDING":
                            node.audit_status = "ROOT_CAUSE_AUDIT_SUGGESTED"
                            if trigger == "ROOT_CAUSE_AUDIT_READY":
                                node.recommended_action = "URGENT_ROOT_CAUSE_AUDIT"
                            else:
                                node.recommended_action = "STRUCTURAL_INVESTIGATION"
            except Exception as e:
                logger.error(f"Failed to generate Heatmap: {e}")
                return []

        return sorted(nodes, key=lambda x: x.friction_score, reverse=True)

    def _calculate_domain_node(self, conn, domain: str) -> HeatmapNode:
        """
        Heuristic calculation of friction score based on real governance signals.
        """
        # 1. Signals Acquisition
        # Debt: Persistent risk acceptance
        debt_count = 0
        try:
            debt_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM governance_risk_overrides WHERE affected_domain = ?", 
                (domain,)
            ).fetchone()["cnt"]
        except: pass
        
        # Advisory: Structural warnings
        adv_count = 0
        try:
            adv_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM governance_rebase_recommendations WHERE affected_domain = ? AND recommendation_state = 'PENDING'", 
                (domain,)
            ).fetchone()["cnt"]
        except: pass

        # Forensics: Tactical effectiveness
        traces = []
        try:
            traces = conn.execute(
                "SELECT outcome_status, severity_delta FROM governance_action_traces WHERE target_domain = ? ORDER BY applied_at DESC LIMIT 15",
                (domain,)
            ).fetchall()
        except: pass
        
        degraded_traces = len([t for t in traces if t["outcome_status"] == 'DEGRADED'])
        effective_traces = len([t for t in traces if t["outcome_status"] == 'EFFECTIVE'])
        avg_delta = sum([t["severity_delta"] for t in traces]) / len(traces) if traces else 0

        # 1.5 Relief & Resistance signals
        relief_status = "NONE"
        relief_baseline = 0.0
        relief_current = 0.0
        relief_outcome = "PENDING"
        try:
            relief_row = conn.execute(
                "SELECT relief_outcome, baseline_friction_score, current_friction_score FROM governance_relief_proposals WHERE source_heatmap_node = ? AND status = 'ACCEPTED' ORDER BY updated_at DESC LIMIT 1",
                (domain,)
            ).fetchone()
            if relief_row:
                relief_status = "ACTIVE"
                relief_outcome = relief_row["relief_outcome"]
                relief_baseline = relief_row["baseline_friction_score"]
                relief_current = relief_row["current_friction_score"]
        except: pass

        # 2. Scoring Algorithm (Heuristic weighting)
        # Weights:
        # Advisory (Critical Warning) = 25 pts
        # Debt (Risk Accepted) = 15 pts
        # Degraded Trace (Intervention Failure) = 20 pts
        # Effective Trace (Relief) = -10 pts
        
        friction_score = 0
        friction_score += (adv_count * 25)
        friction_score += (debt_count * 15)
        friction_score += (degraded_traces * 20)
        friction_score -= (effective_traces * 10)
        
        # Clamp between 0 and 100
        friction_score = max(0, min(100, friction_score))

        # 3. Taxonomy Assignment
        band = "COOL"
        if friction_score > 80:
            band = "CRITICAL"
        elif friction_score > 50:
            band = "HOT"
        elif friction_score > 20:
            band = "WATCH"
        
        # Trend Detection
        # If we have recent effective traces and delta is negative, signal IMPROVING
        if avg_delta < -0.05 and effective_traces > 0 and friction_score < 80:
            band = "IMPROVING"
            
        # Resistance Detection Override
        if relief_outcome == "RESISTANT_HOTSPOT":
            band = "RESISTANT"
        elif relief_outcome == "ESCALATING_DESPITE_RELIEF":
            band = "CRITICAL" # Force critical if escalating despite relief

        # 4. Rationale Construction
        reasons = []
        if adv_count > 0: reasons.append(f"{adv_count} avisos estructurales")
        if debt_count > 0: reasons.append(f"{debt_count} deudas tácticas")
        if degraded_traces > 0: reasons.append(f"{degraded_traces} fallos de alivio")
        
        if relief_status == "ACTIVE":
            reasons.append(f"ALIVIO_{relief_outcome}")
        
        if not reasons:
            rationale = "Dominio estable con señales nominales."
        else:
            rationale = f"Fricción: {', '.join(reasons)}."
            if band == "IMPROVING":
                rationale += " (Tendencia positiva)"
            elif band == "RESISTANT":
                rationale = f"RESISTENCIA DETECTADA. {rationale}"

        # 5. Recommendation Logic
        action = "MONITOR"
        if band == "CRITICAL" or relief_outcome == "ESCALATING_DESPITE_RELIEF":
            action = "ESCALATE_TO_CREATOR_CORE"
        elif band == "RESISTANT":
            action = "OPEN_ROOT_CAUSE_AUDIT"
        elif band == "HOT":
            action = "REBASE_MANDATORY"
        elif band == "WATCH":
            action = "REVIEW_DEBT"
        elif band == "IMPROVING":
            action = "MAINTAIN_STRATEGY"
        
        if relief_outcome == "RELIEF_PENDING" and relief_status == "ACTIVE":
            action = "UNDER_OBSERVATION"

        return HeatmapNode(
            domain=domain,
            friction_score=friction_score,
            severity_band=band,
            rationale=rationale,
            signals={
                "debt_count": debt_count,
                "advisory_count": adv_count,
                "degraded_traces": degraded_traces,
                "effective_traces": effective_traces,
                "relief_status": relief_status,
                "relief_outcome": relief_outcome,
                "relief_baseline": relief_baseline,
                "relief_current": relief_current,
                "avg_delta": round(avg_delta, 2)
            },
            recommended_action=action,
            last_updated=datetime.now().isoformat()
        )

heatmap_engine = GovernanceHeatmapEngine()
