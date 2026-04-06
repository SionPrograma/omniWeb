import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .governance_heatmap_engine import heatmap_engine, HeatmapNode
from .governance_relief_engine import relief_engine, ReliefProposal

logger = logging.getLogger(__name__)

class ReliefEvaluation(BaseModel):
    proposal_id: str
    domain: str
    baseline_score: float
    current_score: float
    delta_score: float
    outcome: str # EFFECTIVE_RELIEF, PARTIAL_RELIEF, NO_VISIBLE_RELIEF, RESISTANT_HOTSPOT, ESCALATING
    rationale: str
    next_action: str
    evaluation_at: str

class GovernanceResistanceEngine:
    """
    OMNIWEB — BLOQUE: GOVERNANCE DRIFT RADAR ENHANCEMENT.
    Evaluates if structural relief missions actually cool down hotspots or if they show resistance.
    """

    def evaluate_all_active_reliefs(self, current_scores: Optional[Dict[str, float]] = None) -> List[ReliefEvaluation]:
        """
        Scans all ACCEPTED relief missions and compares current friction with the baseline.
        """
        evals = []
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # Fetch only active missions
                    rows = conn.execute(
                        "SELECT * FROM governance_relief_proposals WHERE status = 'ACCEPTED'"
                    ).fetchall()
                    
                    if current_scores is None:
                        # Fallback: only if called independently
                        from .governance_heatmap_engine import heatmap_engine
                        current_scores = {n.domain: n.friction_score for n in heatmap_engine.get_friction_heatmap(skip_evaluation=True)}
                    
                    for row in rows:
                        domain = row["source_heatmap_node"]
                        current_score = current_scores.get(domain, 0.0)
                            
                        evaluation = self._perform_evaluation(row, current_score, domain)
                        if evaluation:
                            self._persist_evaluation(conn, evaluation)
                            evals.append(evaluation)
            except Exception as e:
                logger.error(f"Resistance evaluation failure: {e}")
                import traceback
                logger.error(traceback.format_exc())
                        
        return evals

    def _perform_evaluation(self, mission: Dict[str, Any], current: float, domain: str) -> Optional[ReliefEvaluation]:
        """
        Determines the outcome of a relief mission based on the before/after delta.
        """
        baseline = mission["baseline_friction_score"] or 0.0
        
        # If baseline is 0, initialize it (fallback for legacy or race conditions)
        if baseline == 0.0:
            self._update_baseline(mission["proposal_id"], current)
            return None 
            
        delta = current - baseline
        
        # Windows of estimation
        try:
            updated_ts = mission["updated_at"] or mission["created_at"]
            accepted_at = datetime.fromisoformat(updated_ts)
        except:
            accepted_at = datetime.now()
            
        age_hours = (datetime.now() - accepted_at).total_seconds() / 3600
        
        # Tolerance: Under observation for at least 5 minutes in dev/simulation
        if age_hours < 0.08 and mission["observers_count"] == 0:
            return None
            
        outcome = "RELIEF_PENDING"
        rationale = "Evaluando impacto inicial del alivio estructural..."
        next_action = "MAINTAIN_OBSERVATION"
        
        # Heuristics for outcome (Auditado vs Baseline)
        if delta <= -15:
            outcome = "EFFECTIVE_RELIEF"
            rationale = f"Enfriamiento detectable ({delta:.0f} pts). El dominio responde óptimamente al alivio."
            next_action = "CLOSE_OBSERVATION_AS_SUCCESS"
        elif delta <= -5:
            outcome = "PARTIAL_RELIEF"
            rationale = f"Mejora moderada detectada ({delta:.0f} pts). La tendencia es positiva pero requiere monitoreo."
            next_action = "MONITOR_TREND"
        elif abs(delta) <= 5:
            # If no change for more than 2 evaluated steps or > 1 hour
            if mission["observers_count"] >= 3 or age_hours > 2:
                outcome = "NO_VISIBLE_RELIEF"
                rationale = "Sin cambios apreciables tras intervenciones. La fricción se mantiene inerte a pesar del alivio."
                next_action = "REVIEW_MISSION_OBJECTIVES"
            else:
                outcome = "RELIEF_PENDING"
                rationale = f"Sin delta significativo ({delta:+.0f} pts). Manteniendo ventana de observación prudente."
                next_action = "MAINTAIN_OBSERVATION"
        elif delta > 5:
            if delta > 15:
                outcome = "ESCALATING_DESPITE_RELIEF"
                rationale = f"DEGRADACIÓN ACELERADA (+{delta:.0f} pts) a pesar del alivio táctico. Posible falla de arquitectura profunda."
                next_action = "ESCALATE_TO_CREATOR_CORE"
            else:
                outcome = "RELIEF_INEFFECTIVE"
                rationale = f"El calor aumenta ligeramente (+{delta:.0f} pts). El alivio propuesto no está neutralizando la fricción."
                next_action = "OPEN_ROOT_CAUSE_AUDIT"
        
        # Structural Resistance Logic (High score + Time + No improvement)
        if current > 60 and age_hours > 3 and delta >= -3:
            outcome = "RESISTANT_HOTSPOT"
            rationale = "RESISTENCIA ESTRUCTURAL: Dominio no responde al alivio estandarizado. Fricción persistente en niveles críticos."
            next_action = "DECLARE_STRUCTURAL_RESISTANCE"
        
        return ReliefEvaluation(
            proposal_id=mission["proposal_id"],
            domain=domain,
            baseline_score=baseline,
            current_score=current,
            delta_score=delta,
            outcome=outcome,
            rationale=rationale,
            next_action=next_action,
            evaluation_at=datetime.now().isoformat()
        )

    def _update_baseline(self, proposal_id: str, score: float):
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE governance_relief_proposals SET baseline_friction_score = ?, relief_outcome = 'UNDER_OBSERVATION' WHERE proposal_id = ?",
                (score, proposal_id)
            )
            conn.commit()

    def _persist_evaluation(self, conn, ev: ReliefEvaluation):
        # 1. Update proposal main state
        conn.execute(
            """UPDATE governance_relief_proposals 
            SET current_friction_score = ?, relief_outcome = ?, observers_count = observers_count + 1, last_evaluation_at = ? 
            WHERE proposal_id = ?""",
            (ev.current_score, ev.outcome, ev.evaluation_at, ev.proposal_id)
        )
        
        # 2. Log snapshot for history
        conn.execute(
            """INSERT INTO governance_structural_resistance_log 
            (log_id, domain, relief_mission_id, friction_at_start, friction_at_eval, delta, eval_outcome, rationale)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), ev.domain, ev.proposal_id, ev.baseline_score, ev.current_score, ev.delta_score, ev.outcome, ev.rationale)
        )
        conn.commit()

resistance_engine = GovernanceResistanceEngine()
